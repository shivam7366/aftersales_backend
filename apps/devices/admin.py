from django.contrib import admin

# Register your models here.

from .models import Device
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_number', 'serial_number', 'user', 'purchase_date')
    search_fields = ('name', 'model_number', 'serial_number', 'user__email')
    list_filter = ('brand', 'purchase_date')
    ordering = ('-created_at',)
