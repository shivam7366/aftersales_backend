from datetime import date
from rest_framework import serializers
from apps.service_requests.models import (
    ServiceRequest,
    ServiceRequestDocument,
    ServiceRequestActivity,
)


class ServiceRequestActivitySerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequestActivity
        fields = [
            'uuid',
            'user_name',
            'from_status',
            'to_status',
            'comment',
            'created_at',
        ]

    def get_user_name(self, obj):
        if obj.user:
            name = f'{obj.user.first_name} {obj.user.last_name}'.strip()
            return name or obj.user.email
        return 'System'


class ServiceRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = [
            'uuid',
            'device',
            'issue_description',
            'service_type',
            'priority',
            'preferred_visit_date',
            'visit_charge',
            'status',
            'created_at',
        ]
        extra_kwargs = {
            'uuid': {'read_only': True},
            'visit_charge': {'read_only': True},
            'status': {'read_only': True},
            'created_at': {'read_only': True},
        }
    
    def validated_device(self,value):
        request=self.context.get('request')
        if value.user != request.user:
            raise serializers.ValidationError("You can only create service requests for yourself.")
        return value
    
    def validate_preferred_visit_date(self,value):
        if value and value < date.today():
            raise serializers.ValidationError("Preferred visit date cannot be in the past.")
        return value
    
class ServiceRequestListSerializer(serializers.ModelSerializer):
     device_name = serializers.CharField(source='device.name', read_only=True)
     device_brand = serializers.CharField(source='device.brand', read_only=True)

     class Meta:
        model = ServiceRequest
        fields = [
            'uuid',
            'device_name',
            'device_brand',
            'service_type',
            'status',
            'priority',
            'visit_charge',
            'preferred_visit_date',
            'created_at',
        ]

class ServiceRequestDetailSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_brand = serializers.CharField(source='device.brand', read_only=True)
    device_serial = serializers.CharField(source='device.serial_number', read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            'uuid',
            'device',
            'device_name',
            'device_brand',
            'device_serial',
            'issue_description',
            'service_type',
            'status',
            'priority',
            'visit_charge',
            'parts_charge',
            'total_charge',
            'resolution_notes',
            'preferred_visit_date',
            'assigned_to',
            'assigned_to_name',
            'activities',
            'created_at',
            'updated_at',
        ]

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f'{obj.assigned_to.first_name} {obj.assigned_to.last_name}'
        return None

    def get_activities(self, obj):
        qs = obj.activities.select_related('user').order_by('created_at')
        return ServiceRequestActivitySerializer(qs, many=True).data
    
class ServiceRequestDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequestDocument
        fields = [
            'uuid',
            'service_request',
            'file',
            'file_name',
            'description',
            'created_at',
        ]
        extra_kwargs = {
            'uuid': {'read_only': True},
            'created_at': {'read_only': True},
              'service_request': {'read_only': True}, 
              'file_name': {'required': False},
        }
    
    def validae_file(self,value):
        max_size=10*1024*1024

        if value.size>max_size:
            raise serializers.ValidationError('File size can not exceed 10MB.')
        
        allowed_types=['image/jpeg','image/png','image/gif','application/pdf']

        if value.content_type not in allowed_types:
            raise serializers.ValidationError('Unsupported file type. Allowed types are: JPEG, PNG, GIF, PDF.')
    
        return value

    def create(self,validated_data):

        if 'file_name' not in validated_data:
            validated_data['file_name']=validated_data['file'].name
        return super().create(validated_data)