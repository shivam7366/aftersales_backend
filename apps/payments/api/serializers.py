from rest_framework import serializers
from apps.payments.models import Payment


class CreateOrderSerializer(serializers.Serializer):
    service_request_uuid = serializers.UUIDField()
    payment_type = serializers.ChoiceField(choices=Payment.PaymentTypeChoices.choices)


class VerifyPaymentSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()
    payment_uuid = serializers.UUIDField()

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'uuid', 'amount', 'payment_type',
            'status', 'razorpay_order_id',
            'razorpay_payment_id', 
            'created_at', 'updated_at'
        ]
