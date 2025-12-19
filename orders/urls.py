# orders/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.menu, name='menu'),                  # http://localhost:8000/orders/
    path('list/', views.order_list, name='order_list'), # http://localhost:8000/orders/list/
    path('new/', views.order_create, name='order_new'),
    path('edit/<str:pk>/', views.order_edit, name='order_edit'),
    path('branch/<str:pk>/', views.order_branch, name='order_branch'),
]