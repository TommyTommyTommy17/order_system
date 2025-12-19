from django.shortcuts import render, redirect, get_object_or_404
from .models import Order
from .forms import OrderForm
from django.utils import timezone
from django.contrib.auth.decorators import login_required

# 受注一覧
@login_required
def order_list(request):
    today = timezone.now().date()
    orders = Order.objects.filter(issue_date=today).order_by('issue_no')
    return render(request, 'orders/order_list.html', {'orders': orders, 'today': today})

# 新規作成
@login_required
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('order_list')
        else:
            # ★ここを追加：ターミナルにエラーの内容を表示させる
            print("フォームにエラーがあります：", form.errors)
    else:
        form = OrderForm()
    return render(request, 'orders/order_form.html', {'form': form})

# 編集
@login_required
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('order_list')
    else:
        form = OrderForm(instance=order)
    return render(request, 'orders/order_form.html', {'form': form, 'is_edit': True})

# 分岐
@login_required
def order_branch(request, pk):
    original = get_object_or_404(Order, pk=pk)
    prefix = original.issue_no[:6]
    last_branch = Order.objects.filter(issue_no__startswith=prefix).order_by('issue_no').last()
    new_digit = int(last_branch.issue_no[6]) + 1
    
    if new_digit > 9:
        return redirect('order_list') # 枝番オーバーは一旦無視

    # クローン作成
    original.pk = f"{prefix}{new_digit}"
    original.issue_date = timezone.now().date()
    original.save()
    return redirect('order_edit', pk=original.pk)

# メニュー画面
@login_required
def menu(request):
    return render(request, 'orders/menu.html')