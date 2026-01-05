# orders/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.menu, name='menu'),                  # http://localhost:8000/orders/
    path('list/', views.order_list, name='order_list'), # http://localhost:8000/orders/list/
    path('new/', views.order_create, name='order_new'),
    path('edit/<str:pk>/', views.order_edit, name='order_edit'),
    path('branch/<str:pk>/', views.order_branch, name='order_branch'),
    path('schedule/', views.schedule_board, name='schedule_board'),
    path('autocomplete/', views.order_autocomplete, name='order_autocomplete'),
    path('save_plan/', views.save_plan, name='save_plan'),  
    path('get_plans/', views.get_plans, name='get_plans'),
    path('shipment/new/', views.shipment_create, name='shipment_create'),
    path('api/shipment-stats/', views.get_shipment_stats, name='get_shipment_stats'),
]