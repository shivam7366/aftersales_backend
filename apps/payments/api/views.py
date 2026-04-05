from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.conf import settings
from apps.payments.api.serializers import CreateOrderSerializer, VerifyPaymentSerializer, PaymentSerializer
from apps.payments.models import Payment
from apps.payments.services import RazorpayService
from apps.common.permissions import IsCustomer
from apps.service_requests.models import ServiceRequest


class CreateOrderView(APIView):
    permission_classes = [IsCustomer]
    def post(self, request):
        serializer=CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service_request_uuid=serializer.validated_data['service_request_uuid']
        payment_type=serializer.validated_data['payment_type']

        service_request=get_object_or_404(ServiceRequest, uuid=service_request_uuid, customer=request.user)

        allowed_statuses = [
    ServiceRequest.StatusChoices.PENDING,
    ServiceRequest.StatusChoices.VISIT_CHARGE_PENDING,
    ServiceRequest.StatusChoices.QUOTE_PAYMENT_PENDING,
]

        if service_request.status not in allowed_statuses:
            return Response(
        {'error': 'Service request is not in a valid state for payment.'},
        status=status.HTTP_400_BAD_REQUEST
    )

        if service_request.payment_status!=Payment.PaymentStatusChoices.PENDING:
            return Response({'error': 'Payment is already completed.'}, status=status.HTTP_400_BAD_REQUEST)

        amount=service_request.visit_charge if payment_type==Payment.PaymentTypeChoices.VISIT_CHARGE else service_request.total_charge

        razorpay_service=RazorpayService()
        order_data=razorpay_service.create_order(float(amount))

        payment=Payment.objects.create(
            service_request=service_request,
            amount=amount,
            payment_type=payment_type,
            payment_method='razorpay',
            transaction_id=order_data['id'],
            status=Payment.PaymentStatusChoices.PENDING,
            payment_gateway_response=order_data,
            razorpay_order_id=order_data['id'],
            razorpay_payment_id=None,
            razorpay_signature=None,
        )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class VerifyPaymentView(APIView):

    permission_classes = [IsCustomer]
    def post(self, request):
        serializer=VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        razorpay_order_id=serializer.validated_data['razorpay_order_id']
        razorpay_payment_id=serializer.validated_data['razorpay_payment_id']
        razorpay_signature=serializer.validated_data['razorpay_signature']
        payment_uuid=serializer.validated_data['payment_uuid']
        
        payment=get_object_or_404(Payment, uuid=payment_uuid, service_request__customer=request.user)

        if payment.status!=Payment.PaymentStatusChoices.PENDING:
            return Response({'error': 'Payment is not pending.'}, status=status.HTTP_400_BAD_REQUEST)

        if payment.razorpay_order_id!=razorpay_order_id:
            return Response({'error': 'Invalid razorpay order id.'}, status=status.HTTP_400_BAD_REQUEST)

        # if payment.razorpay_payment_id!=razorpay_payment_id:
        #     return Response({'error': 'Invalid razorpay payment id.'}, status=status.HTTP_400_BAD_REQUEST)
            
        razorpay_service=RazorpayService()
        is_verified=razorpay_service.verfiy_signature(razorpay_order_id,razorpay_payment_id,razorpay_signature)
        if not is_verified:
            return Response({'error': 'Invalid razorpay signature.'}, status=status.HTTP_400_BAD_REQUEST)

        payment.razorpay_payment_id=razorpay_payment_id
        payment.razorpay_signature=razorpay_signature
        payment.status=Payment.PaymentStatusChoices.COMPLETED
        payment.save()
        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)