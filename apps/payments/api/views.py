from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from apps.payments.api.serializers import (
    CreateOrderSerializer,
    VerifyPaymentSerializer,
    PaymentSerializer,
)
from apps.payments.models import Payment
from apps.payments.services import RazorpayService
from apps.common.permissions import IsCustomer
from apps.service_requests.models import ServiceRequest
from apps.service_requests.services import ActivityLogService


class CreateOrderView(APIView):
    permission_classes = [IsCustomer]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service_request_uuid = serializer.validated_data['service_request_uuid']
        payment_type = serializer.validated_data['payment_type']

        service_request = get_object_or_404(
            ServiceRequest, uuid=service_request_uuid, customer=request.user
        )

        if payment_type == Payment.PaymentTypeChoices.VISIT_CHARGE:
            visit_allowed = [
                ServiceRequest.StatusChoices.PENDING,
                ServiceRequest.StatusChoices.VISIT_CHARGE_PENDING,
            ]
            if service_request.status not in visit_allowed:
                return Response(
                    {
                        'error': (
                            'Visit charge payment is only allowed when the request '
                            'is pending or visit charge pending.'
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if Payment.objects.filter(
                service_request=service_request,
                payment_type=Payment.PaymentTypeChoices.VISIT_CHARGE,
                status=Payment.PaymentStatusChoices.COMPLETED,
            ).exists():
                return Response(
                    {'error': 'Visit charge is already paid.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            amount = service_request.visit_charge
            if amount is None or float(amount) <= 0:
                return Response(
                    {'error': 'No visit charge due for this request.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif payment_type == Payment.PaymentTypeChoices.PARTS_CHARGE:
            parts_allowed = [
                ServiceRequest.StatusChoices.QUOTE_APPROVED,
            ]
            if service_request.status not in parts_allowed:
                return Response(
                    {
                        'error': (
                            'Parts payment is only allowed after the quote is '
                            'approved (pay parts charge only; total is informational).'
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            amount = service_request.parts_charge
            if amount is None or float(amount) <= 0:
                return Response(
                    {'error': 'No parts charge on this quote.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if Payment.objects.filter(
                service_request=service_request,
                payment_type=Payment.PaymentTypeChoices.PARTS_CHARGE,
                status=Payment.PaymentStatusChoices.PENDING,
            ).exists():
                return Response(
                    {'error': 'A parts payment is already in progress.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {
                    'error': (
                        'Only visit_charge and parts_charge can be paid. '
                        'Total charge is not a separate payment.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        razorpay_service = RazorpayService()
        order_data = razorpay_service.create_order(float(amount))

        payment = Payment.objects.create(
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
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        razorpay_order_id = serializer.validated_data['razorpay_order_id']
        razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
        razorpay_signature = serializer.validated_data['razorpay_signature']
        payment_uuid = serializer.validated_data['payment_uuid']

        payment = get_object_or_404(
            Payment, uuid=payment_uuid, service_request__customer=request.user
        )
        service_request = get_object_or_404(
            ServiceRequest,
            uuid=payment.service_request.uuid,
            customer=request.user,
        )

        if payment.payment_type not in (
            Payment.PaymentTypeChoices.VISIT_CHARGE,
            Payment.PaymentTypeChoices.PARTS_CHARGE,
        ):
            return Response(
                {'error': 'Invalid payment type for verification.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.status != Payment.PaymentStatusChoices.PENDING:
            return Response(
                {'error': 'Payment is not pending.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment.razorpay_order_id != razorpay_order_id:
            return Response(
                {'error': 'Invalid razorpay order id.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        razorpay_service = RazorpayService()
        is_verified = razorpay_service.verfiy_signature(
            razorpay_order_id, razorpay_payment_id, razorpay_signature
        )
        if not is_verified:
            return Response(
                {'error': 'Invalid razorpay signature.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = Payment.PaymentStatusChoices.COMPLETED

        old_status = service_request.status

        payment.save()

        if payment.payment_type == Payment.PaymentTypeChoices.VISIT_CHARGE:
            new_status = ServiceRequest.StatusChoices.VISIT_CHARGE_PAID
        else:
            new_status = ServiceRequest.StatusChoices.QUOTE_PAYMENT_PAID

        service_request.status = new_status
        service_request.save()

        type_label = dict(Payment.PaymentTypeChoices.choices).get(
            payment.payment_type, payment.payment_type
        )
        ActivityLogService.log_activity(
            service_request=service_request,
            user=request.user,
            from_status=old_status,
            to_status=new_status,
            comment=(
                f'Payment completed ({type_label}): ₹{payment.amount} via Razorpay. '
                f'Transaction verified.'
            ),
        )

        return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)
