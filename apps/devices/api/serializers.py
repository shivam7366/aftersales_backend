from rest_framework import serializers
from apps.devices.models import Device


class DeviceSerializer(serializers.ModelSerializer):
    '''Serializer for the Device model, used to convert device instances to and from JSON format for API responses and requests.'''


    class Meta:
        model=Device

        fields=[
            'uuid',
            'name',
            'brand',
            'model_number',
            'serial_number',
            'description',
            'purchase_date',
        ]
        extra_kwargs={
            'uuid': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }
   
