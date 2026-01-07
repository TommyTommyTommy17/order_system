import json
import math
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from django.utils import timezone
from django.db import models
from django.contrib.auth.decorators import user_passes_test
from .forms import StaffForm, SystemConfigForm

# モデルとフォームのインポート（UnitPriceMasterを追加）
from .models import Order, OrderPlan, Shipment, UnitPriceMaster
from .forms import OrderForm, ShipmentForm

from .models import User, SystemConfig 
from django.contrib.auth import get_user_model

# --- 基本画面 ---
@login_required
def menu(request):
    """メインメニュー"""
    return render(request, 'orders/menu.html')

@login_required
def schedule_board(request):
    """出荷予定管理ボード"""
    return render(request, 'orders/schedule_board.html')

# --- 受注管理 ---
@login_required
def order_list(request):
    """受注案件一覧"""
    orders = Order.objects.all().order_by('-issue_no')
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def order_create(request):
    """新規受注作成"""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('order_list')
    else:
        form = OrderForm()
    return render(request, 'orders/order_form.html', {'form': form})

@login_required
def order_edit(request, pk):
    """受注内容編集"""
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('order_list')
    else:
        form = OrderForm(instance=order)
    return render(request, 'orders/order_form.html', {'form': form})

@login_required
def order_branch(request, pk):
    """既存の受注をベースに枝番（コピー）を作成"""
    parent_order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('order_list')
    
    base_no = parent_order.issue_no[:6]
    last_order = Order.objects.filter(issue_no__startswith=base_no).order_by('-issue_no').first()
    try:
        new_branch = int(last_order.issue_no[6:]) + 1
    except (ValueError, IndexError):
        new_branch = 1
    new_issue_no = f"{base_no}{new_branch}"

    initial_data = model_to_dict(parent_order)
    initial_data['issue_no'] = new_issue_no
    initial_data['issue_date'] = parent_order.issue_date
    initial_data['firstship_date'] = parent_order.firstship_date

    form = OrderForm(initial=initial_data)
    return render(request, 'orders/order_form.html', {
        'form': form, 
        'is_branch': True, 
        'parent_no': parent_order.issue_no
    })

# --- API ---
@login_required
def order_autocomplete(request):
    """オートコンプリート（現場名・契約NO検索）"""
    term = request.GET.get('term', '')
    results = []
    if term:
        orders = Order.objects.filter(
            Q(site__icontains=term) | Q(issue_no__icontains=term)
        ).order_by('site')[:15]
        for o in orders:
            results.append({
                'issue_no': o.issue_no, 
                'site': o.site, 
                'address': o.site_address
            })
    return JsonResponse(results, safe=False)

@csrf_exempt
@login_required
def save_plan(request):
    """予定のリアルタイム保存（重複防止版）"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            def to_float(val):
                if not val or not str(val).strip(): return None
                try: return float(val)
                except: return None

            def to_int(val):
                if not val or not str(val).strip(): return None
                try: return int(val)
                except: return None

            row_idx = to_int(data.get('row_index'))
            
            plan, created = OrderPlan.objects.update_or_create(
                plan_date=data['date'],
                section=data['section'],
                row_index=row_idx,
                defaults={
                    'site_name': data.get('site', ''),
                    'start_time': data.get('time', ''),
                    'plan_qty': to_float(data.get('qty')),
                    'truck_count': to_int(data.get('truck')),
                    'plan_note': data.get('note', ''),
                    'order': Order.objects.filter(issue_no=data.get('issue_no')).first() if data.get('issue_no') else None
                }
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'POSTが必要です'}, status=400)

@login_required
def get_plans(request):
    """全予定の取得"""
    plans = OrderPlan.objects.all()
    results = []
    for p in plans:
        results.append({
            'date': p.plan_date.strftime('%Y-%m-%d'),
            'section': p.section,
            'row_index': p.row_index,
            'site': p.site_name,
            'time': p.start_time,
            'qty': p.plan_qty,
            'truck': p.truck_count,
            'note': p.plan_note,
            'issue_no': p.order.issue_no if p.order else ''
        })
    return JsonResponse(results, safe=False)

# --- 実績管理・単価マスタ ---
@login_required
def daily_performance_report(request):
    """実績管理表の集計"""
    target_date_str = request.GET.get('date', timezone.localtime().date().isoformat())
    target_date = timezone.datetime.strptime(target_date_str, '%Y-%m-%d').date()

    issue_numbers = Shipment.objects.filter(ship_date=target_date).values_list('issue_no', flat=True).distinct()
    report_data = []

    for no in issue_numbers:
        shipments = Shipment.objects.filter(ship_date=target_date, issue_no=no)
        order = Order.objects.filter(issue_no=no).first()
        if not order: continue

        N = shipments.count()
        k_val = OrderPlan.objects.filter(plan_date=target_date, order__issue_no=no).aggregate(Sum('truck_count'))['truck_count__sum'] or 1
        
        L = math.ceil(N / k_val)
        M = math.floor(N / k_val)
        Q = N // k_val
        R = N % k_val
        X = (Q + 1) * R
        Y = Q * (k_val - R)

        short_diff = 0
        for s in shipments:
            if s.ship_qty < 6.0:
                short_diff += (6.0 - s.ship_qty)

        price_X = get_price_from_master(L, order.night)
        price_Y = get_price_from_master(M, order.night)
        price_empty = get_price_from_master(L, order.night, is_empty=True)

        report_data.append({
            'issue_no': no,
            'truck_planned': k_val,
            'customer': order.customer,
            'site': order.site,
            'rows': [
                {'item': f'流動化処理土 出荷量㎥ ({L}回転)', 'unit': X, 'price': price_X, 'total': X * 6 - short_diff},
                {'item': f'流動化処理土 出荷量㎥ ({M}回転)', 'unit': Y, 'price': price_Y, 'total': Y * 6},
                {'item': '空積割増', 'unit': L if short_diff > 0 else 0, 'price': price_empty, 'total': short_diff},
            ]
        })

    return render(request, 'orders/daily_report.html', {'report_data': report_data, 'target_date': target_date})

def get_price_from_master(rotation, is_night, is_empty=False):
    """単価取得用ヘルパー"""
    prefix = "夜間" if is_night else "昼間"
    suffix = f"{rotation}回空積" if is_empty else f"{rotation}回転"
    master = UnitPriceMaster.objects.filter(item_name=f"{prefix} {suffix}").first()
    return master.partition_price if master else 0

@login_required
def master_setting(request):
    """単価マスタ設定画面 (一括保存・行追加・削除対応)"""
    if request.method == 'POST':
        action = request.POST.get('action')
        delete_id = request.POST.get('delete_id')

        # 1. 行の削除処理
        if delete_id:
            UnitPriceMaster.objects.filter(id=delete_id).delete()
            return redirect('master_setting')

        # 2. 新しい行の追加処理
        if action == 'add':
            UnitPriceMaster.objects.create(
                category="新規区分", 
                item_name="新規項目", 
                partition_price=0, 
                standard_price=0
            )
            return redirect('master_setting')

        # 3. 一括保存処理
        if action == 'save':
            # 画面上の全IDを特定するために、price_ で始まるキーを抽出
            ids = [k.split('_')[1] for k in request.POST.keys() if k.startswith('price_')]
            for mid in ids:
                UnitPriceMaster.objects.filter(id=mid).update(
                    category=request.POST.get(f'cat_{mid}'),
                    item_name=request.POST.get(f'name_{mid}'),
                    partition_price=int(request.POST.get(f'price_{mid}', 0) or 0),
                    standard_price=int(request.POST.get(f'std_{mid}', 0) or 0)
                )
            return redirect('master_setting')

    masters = UnitPriceMaster.objects.all().order_by('category', 'id')
    return render(request, 'orders/master_setting.html', {'masters': masters})

# --- 出荷入力・統計 ---
@login_required
def shipment_create(request):
    """出荷実績入力"""
    issue_no = request.GET.get('issue_no')
    now = timezone.localtime() 
    current_time = now.strftime('%H:%M') 
    today = now.date()

    initial_data = {
        'ship_date': today,
        'ship_time': current_time, 
        'ship_qty': 6.0,
    }

    if issue_no:
        order = Order.objects.filter(issue_no=issue_no).first()
        if order:
            total_shipped = Shipment.objects.filter(issue_no=issue_no).aggregate(models.Sum('ship_qty'))['ship_qty__sum'] or 0
            initial_data.update({
                'issue_no': order.issue_no,
                'contract_qty': order.qty,
                'remaining_qty': order.qty - (total_shipped + 6.0),
                'site': order.site,
                'site_address': order.site_address,
                'customer': order.customer,
                'contractor': order.contractor,
                'coordinator': order.coordinator.display_name if order.coordinator else "",
                'contact': order.contact,
                'product': order.product,
                'product_category': order.product_category,
                'price': order.price,
                'rotation': order.rotation,
                'material_soil': order.material_soil,
                'water': order.water,
                'cementBB': order.cementBB,
                'recycle_sand': order.recycle_sand,
                'admixture': order.admixture,
                'material_soil_wm': order.material_soil_wm,
                'test': order.test,
                'night': order.night,
                'outside23': order.outside23,
                'material_delivery': order.material_delivery,
                'note': order.note,
                'specialnote': order.specialnote,
            })
            
            today_ships = Shipment.objects.filter(issue_no=issue_no, ship_date=now.date()).order_by('id')
            initial_data['total_unit'] = today_ships.count() + 1
            initial_data['total_ship_qty'] = (today_ships.aggregate(models.Sum('ship_qty'))['ship_qty__sum'] or 0) + 6.0
            last_ship = today_ships.last()
            if last_ship:
                initial_data['before_car_no'] = last_ship.car_no

    if request.method == 'POST':
        form = ShipmentForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'orders/shipment_form.html', {'saved_success': True})
    else:
        form = ShipmentForm(initial=initial_data)

    return render(request, 'orders/shipment_form.html', {'form': form})

@login_required
def get_shipment_stats(request):
    """リアルタイム出荷統計取得API"""
    issue_no = request.GET.get('issue_no')
    today = timezone.now().date()
    order = Order.objects.filter(issue_no=issue_no).first()
    if not order:
        return JsonResponse({'error': '受注が見つかりません'}, status=404)

    prev_shipments = Shipment.objects.filter(issue_no=issue_no, ship_date=today).order_by('id')
    total_unit = prev_shipments.count() + 1
    total_ship_qty_sum = prev_shipments.aggregate(Sum('ship_qty'))['ship_qty__sum'] or 0
    last_ship = prev_shipments.last()
    before_car_no = last_ship.car_no if last_ship else "なし"

    return JsonResponse({
        'total_unit': total_unit,
        'total_ship_qty': total_ship_qty_sum + 6.0,
        'before_car_no': before_car_no,
        'site': order.site,
        'customer': order.customer,
        'product': order.product,
        'site_address': order.site_address,
        'coordinator': order.coordinator.display_name if order.coordinator else "",
    })

def admin_check(user):
    return user.is_authenticated and user.is_admin_user

@user_passes_test(admin_check)
def staff_master_list(request):
    """
    管理者のみ：担当者一覧とパスワード変更
    """
    staff_users = User.objects.all()
    return render(request, 'orders/staff_master.html', {'staff_users': staff_users})

@user_passes_test(admin_check)
def update_system_config(request):
    """
    管理者のみ：タイムアウト時間 $N$ の変更
    """
    config = SystemConfig.objects.first()
    # POST処理で config.session_timeout_minutes を更新

def admin_check(user):
    return user.is_authenticated and user.is_admin_user

@user_passes_test(admin_check)
def staff_management(request):
    """担当者管理・システム設定"""
    users = User.objects.all().order_by('-is_admin_user', 'username')
    config = SystemConfig.objects.first()
    
    if request.method == 'POST':
        # タイムアウト設定の更新
        if 'update_config' in request.POST:
            config_form = SystemConfigForm(request.POST, instance=config)
            if config_form.is_valid():
                config_form.save()
                return redirect('staff_management')
        
        # 新規ユーザー登録
        if 'create_user' in request.POST:
            form = StaffForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password']) # パスワードをハッシュ化して保存
                user.save()
                return redirect('staff_management')

    return render(request, 'orders/staff_management.html', {
        'staff_users': users,
        'config': config,
        'form': StaffForm()
    })

@user_passes_test(admin_check)
def reset_password(request, pk):
    """管理者によるパスワード強制変更"""
    target_user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        new_pass = request.POST.get('new_password')
        if new_pass:
            target_user.set_password(new_pass)
            target_user.save()
    return redirect('staff_management')