import json
import math
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from .models import Order, OrderPlan, Shipment
from .forms import OrderForm, ShipmentForm
from django.db.models import Sum
from .forms import ShipmentForm
from django.utils import timezone
from django.db import models

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
    
    # 契約NOの枝番計算
    base_no = parent_order.issue_no[:6]
    last_order = Order.objects.filter(issue_no__startswith=base_no).order_by('-issue_no').first()
    try:
        new_branch = int(last_order.issue_no[6:]) + 1
    except (ValueError, IndexError):
        new_branch = 1
    new_issue_no = f"{base_no}{new_branch}"

    # 元データを全コピー
    initial_data = model_to_dict(parent_order)
    initial_data['issue_no'] = new_issue_no
    # 日付型が辞書変換で落ちる場合があるため明示的に再代入
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

            # 重要：row_indexを数値に変換することで、DB上の既存レコードを確実に特定
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

@login_required
def shipment_create(request):
    issue_no = request.GET.get('issue_no')
    
    # 修正ポイント:確実に東京の時間(settings.TIME_ZONE)を取得
    now = timezone.localtime() 
    
    # %H は24時間表記（00-23）、%M は分（00-59）
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
            # 総出荷量の計算
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
            
            # 本日の累計台数等の取得
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
            # 保存成功時にフラグを返してJavaScriptを発火させる
            return render(request, 'orders/shipment_form.html', {'saved_success': True})
    else:
        form = ShipmentForm(initial=initial_data)

    return render(request, 'orders/shipment_form.html', {'form': form})

@login_required
def get_shipment_stats(request):
    """
    契約NOに基づき、本日の累計台数、累計出荷量、前車NO、および受注情報を返す
    """
    issue_no = request.GET.get('issue_no')
    today = timezone.now().date()
    
    # 1. 受注情報の取得
    order = Order.objects.filter(issue_no=issue_no).first()
    if not order:
        return JsonResponse({'error': '受注が見つかりません'}, status=404)

    # 2. 本日の出荷実績から統計を計算
    prev_shipments = Shipment.objects.filter(issue_no=issue_no, ship_date=today).order_by('id')
    
    total_unit = prev_shipments.count() + 1  # 次の台数
    total_ship_qty_sum = prev_shipments.aggregate(Sum('ship_qty'))['ship_qty__sum'] or 0
    
    last_ship = prev_shipments.last()
    before_car_no = last_ship.car_no if last_ship else "なし" # 前車NO

    return JsonResponse({
        'total_unit': total_unit,
        'total_ship_qty': total_ship_qty_sum + 6.0, # 初期出荷量6を含む累計
        'before_car_no': before_car_no,
        # 受注情報のコピー
        'site': order.site,
        'customer': order.customer,
        'product': order.product,
        'site_address': order.site_address,
        'coordinator': order.coordinator.display_name if order.coordinator else "",
        # 必要に応じて他の項目を追加
    })

