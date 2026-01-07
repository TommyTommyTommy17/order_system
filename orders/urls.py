from django.urls import path
from . import views

urlpatterns = [
    # --- メインメニュー ---
    # アクセス先: http://localhost:8000/orders/menu/
    path('menu/', views.menu, name='menu'),

    # --- 受注案件管理 ---
    # アクセス先: http://localhost:8000/orders/
    path('', views.order_list, name='order_list'), 
    # アクセス先: http://localhost:8000/orders/new/
    path('new/', views.order_create, name='order_new'),
    # アクセス先: http://localhost:8000/orders/edit/1/
    path('edit/<int:pk>/', views.order_edit, name='order_edit'),
    # アクセス先: http://localhost:8000/orders/branch/1/
    path('branch/<int:pk>/', views.order_branch, name='order_branch'),

    # --- 出荷予定（スケジュールボード） ---
    # アクセス先: http://localhost:8000/orders/schedule/
    path('schedule/', views.schedule_board, name='schedule_board'),
    # アクセス先: http://localhost:8000/orders/get_plans/
    path('get_plans/', views.get_plans, name='get_plans'),
    # アクセス先: http://localhost:8000/orders/save_plan/
    path('save_plan/', views.save_plan, name='save_plan'),
    # アクセス先: http://localhost:8000/orders/autocomplete/
    path('autocomplete/', views.order_autocomplete, name='autocomplete'),

    # --- 出荷入力・統計 ---
    # アクセス先: http://localhost:8000/orders/shipment/create/
    path('shipment/create/', views.shipment_create, name='shipment_create'),
    # アクセス先: http://localhost:8000/orders/shipment/stats/
    path('shipment/stats/', views.get_shipment_stats, name='get_shipment_stats'),

    # --- 実績管理表・単価マスタ ---
    # アクセス先: http://localhost:8000/orders/performance-report/
    path('performance-report/', views.daily_performance_report, name='daily_performance_report'),
    # アクセス先: http://localhost:8000/orders/master-setting/
    path('master-setting/', views.master_setting, name='master_setting'),

    # orders/urls.py に追記
    path('staff-management/', views.staff_management, name='staff_management'),
    path('reset-password/<int:pk>/', views.reset_password, name='reset_password'),
]