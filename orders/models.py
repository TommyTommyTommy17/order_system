import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# 担当者マスタ
class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=50, verbose_name="担当者名")
    def __str__(self):
        return self.display_name

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
            year_prefix = str(datetime.datetime.now().year)[2:]
            last_order = Order.objects.filter(issue_no__startswith=year_prefix).order_by('issue_no').last()
            if last_order:
                last_seq = int(last_order.issue_no[2:6])
                new_seq = str(last_seq + 1).zfill(4)
            else:
                new_seq = "0001"
            self.issue_no = f"{year_prefix}{new_seq}0"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.issue_no} / {self.site}"

# 出荷テーブル（ここを追加したことでImportErrorが消えます）
class Shipment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='shipments', verbose_name="受注紐付")
    ship_date = models.DateField(default=timezone.now, verbose_name="出荷日")
    ship_time = models.TimeField(verbose_name="出荷時間")
    ship_qty = models.FloatField(verbose_name="出荷量")
    car_no = models.CharField(max_length=50, verbose_name="車両番号")
    total_unit = models.IntegerField(verbose_name="累計台数")
    total_ship_qty = models.FloatField(verbose_name="累計出荷量")
    before_car_no = models.CharField(max_length=50, blank=True, verbose_name="前車NO")

    def __str__(self):
        return f"{self.order.issue_no} - {self.ship_date}"