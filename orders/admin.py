from django.contrib import admin
from .models import Staff, Order, Shipment

admin.site.register(Staff)
admin.site.register(Order)

admin.site.register(Shipment)