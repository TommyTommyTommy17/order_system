import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser,User
from django.utils import timezone
from django.conf import settings

# 担当者マスタ
class Staff(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='staff_profile'
    )

class User(AbstractUser):
    is_admin_user = models.BooleanField('管理者権限', default=False)
    display_name = models.CharField('表示名', max_length=50, blank=True)

# 受注テーブル
class Order(models.Model):
    issue_no = models.CharField(max_length=7, primary_key=True, blank=True, verbose_name="契約NO")
    issue_date = models.DateField(default=timezone.now, verbose_name="契約日")
    site = models.CharField(max_length=200, verbose_name="現場名")
    site_address = models.CharField(max_length=255, verbose_name="現場住所")
    customer = models.CharField(max_length=200, verbose_name="得意先")
    contractor = models.CharField(max_length=200, verbose_name="施工者名")
    coordinator = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, verbose_name="担当者名")
    contact = models.CharField(max_length=100, verbose_name="連絡先")
    product = models.CharField(max_length=100, verbose_name="商品名")
    product_category = models.CharField(max_length=100, verbose_name="商品区分")
    note = models.TextField(blank=True, verbose_name="備考")
    firstship_date = models.DateField(verbose_name="初回出荷予定日")
    qty = models.FloatField(verbose_name="契約数量")
    rotation = models.IntegerField(verbose_name="予定回転数")
    price = models.IntegerField(verbose_name="販売単価")

    # 配合データ
    material_soil = models.CharField(max_length=100, blank=True, verbose_name="原料土")
    water = models.FloatField(default=0, verbose_name="水")
    cementBB = models.FloatField(default=0, verbose_name="セメントBB")
    recycle_sand = models.FloatField(default=0, verbose_name="再生砂")
    admixture = models.FloatField(default=0, verbose_name="混和剤")
    material_soil_wm = models.FloatField(default=0, verbose_name="原料土wm")

    # 判定フラグ
    test = models.BooleanField(default=False, verbose_name="現場試験")
    night = models.BooleanField(default=False, verbose_name="夜間")
    outside23 = models.BooleanField(default=False, verbose_name="23区外")
    material_delivery = models.BooleanField(default=False, verbose_name="材料渡し")
    specialnote = models.TextField(blank=True, verbose_name="特記項目")

    def save(self, *args, **kwargs):
        if not self.issue_no:
            # 現在の西暦の下2桁（例: 2025年 -> "25"）
            year_prefix = str(datetime.datetime.now().year)[2:]
            # その年の最新レコードを取得
            last_order = Order.objects.filter(issue_no__startswith=year_prefix).order_by('issue_no').last()
            
            if last_order:
                # 最新の連番（25XXXX0 の XXXX部分）を抽出して+1
                last_seq = int(last_order.issue_no[2:6])
                new_seq = str(last_seq + 1).zfill(4)
            else:
                new_seq = "0001"
            
            # 新規登録時は最後に "0" を付与
            self.issue_no = f"{year_prefix}{new_seq}0"
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.issue_no} / {self.site}"

# 出荷テーブル（ここを追加したことでImportErrorが消えます）
class Shipment(models.Model):
    # 基本情報
    issue_no = models.CharField('契約NO', max_length=10, default='') 
    ship_date = models.DateField('出荷日', default=timezone.now)
    ship_time = models.TimeField('出荷時間', default=timezone.now)
    ship_qty = models.FloatField('出荷量', default=6.0)
    car_no = models.CharField('車両番号', max_length=3, default='')
    
    # 統計情報
    total_unit = models.IntegerField('累計台数', default=0)
    total_ship_qty = models.FloatField('累計出荷量', default=0.0)
    before_car_no = models.CharField('前車NO', max_length=3, blank=True, default='')
    contract_qty = models.FloatField('契約数量', default=0)
    remaining_qty = models.FloatField('残量', default=0)
    
    # 受注からのコピー項目
    site = models.CharField('現場名', max_length=100, default='')
    site_address = models.CharField('現場住所', max_length=200, blank=True, default='')
    customer = models.CharField('得意先', max_length=100, default='')
    contractor = models.CharField('施工者名', max_length=100, blank=True, default='')
    coordinator = models.CharField('担当者名', max_length=50, blank=True, default='')
    contact = models.CharField('連絡先', max_length=50, blank=True, default='')
    product = models.CharField('商品名', max_length=100, default='')
    product_category = models.CharField('標準/規格', max_length=100, blank=True, default='')
    note = models.TextField('備考', blank=True, default='')
    specialnote = models.TextField('特記事項', blank=True, default='')
    
    # 【修正：任意入力化】数値項目に null=True, blank=True を追加
    rotation = models.FloatField('予定回転数', default=0, null=True, blank=True)
    price = models.IntegerField('販売単価', default=0, null=True, blank=True)
    material_soil = models.FloatField('原料土', default=0, null=True, blank=True)
    water = models.FloatField('水', default=0, null=True, blank=True)
    cementBB = models.FloatField('セメントBB', default=0, null=True, blank=True)
    recycle_sand = models.FloatField('再生砂', default=0, null=True, blank=True)
    admixture = models.FloatField('混和剤', default=0, null=True, blank=True)
    material_soil_wm = models.FloatField('原料土wm', default=0, null=True, blank=True)
    
    # 真偽値項目
    test = models.BooleanField('現場試験', default=False)
    night = models.BooleanField('夜間', default=False)
    outside23 = models.BooleanField('23区外', default=False)
    material_delivery = models.BooleanField('材料渡し', default=False)
    
class OrderPlan(models.Model):
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    plan_date = models.DateField()
    section = models.CharField(max_length=10) # 'el' または 'other'
    row_index = models.IntegerField()
    site_name = models.CharField(max_length=200, blank=True)
    start_time = models.CharField(max_length=10, blank=True)
    plan_qty = models.FloatField(null=True, blank=True)
    truck_count = models.IntegerField(null=True, blank=True)
    plan_note = models.TextField(blank=True)

    class Meta:
        unique_together = ('plan_date', 'section', 'row_index')

    def __str__(self):
        return f"{self.plan_date} [{self.section}-{self.row_index}] {self.site_name}"

    # 契約数量チェック用のロジック（後で活用します）
    def check_over_qty(self):
        # 同じ契約NOの予定合計を算出
        total_planned = OrderPlan.objects.filter(order=self.order).aggregate(models.Sum('plan_qty'))['plan_qty__sum'] or 0
        return total_planned > self.order.qty

# orders/models.py

class UnitPriceMaster(models.Model):
    category = models.CharField('区分', max_length=50)  # 昼間、夜間、空積、その他
    item_name = models.CharField('項目名', max_length=100) # 昼間 1回転、昼間 1回空積 など
    partition_price = models.IntegerField('仕切り価格')  # 実績管理表で使用する単価
    standard_price = models.IntegerField('標準販売価格', default=0)
    
    class Meta:
        verbose_name = "単価マスタ"

    def __str__(self):
        return f"{self.item_name}: {self.partition_price}円"


class SystemConfig(models.Model):
    """
    システム全体の設定（タイムアウト時間 $N$ など）
    """
    session_timeout_minutes = models.IntegerField('セッション有効期限(分)', default=30)

    class Meta:
        verbose_name = 'システム設定'