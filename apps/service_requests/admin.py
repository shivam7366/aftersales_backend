from django.contrib import admin
from .models import ServiceRequest


# Register your models here.

@admin.register(ServiceRequest)

class ServiceRequestAdmin(admin.ModelAdmin):
    list_display=('uuid','status','priority','customer','assigned_to')
    search_fields = ('uuid', 'customer', 'assigned_to')
    list_filter = ('status', 'priority')
    ordering = ('-created_at',)
    