import uuid
from django.db import models
from apps.common.models import TimeStampMixin


class Payment(TimeStampMixin):
    class PaymentTypeChoices(models.TextChoices):
        VISIT_CHARGE = 'visit_charge', 'Visit Charge'
        PARTS_CHARGE = 'parts_charge', 'Parts Charge'
        TOTAL_CHARGE = 'total_charge', 'Total Charge'

    class PaymentStatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.ForeignKey(
        'service_requests.ServiceRequest',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PaymentTypeChoices.choices, default=PaymentTypeChoices.TOTAL_CHARGE)
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=PaymentStatusChoices.choices, default=PaymentStatusChoices.PENDING)
    payment_gateway_response = models.JSONField(blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.payment_type} - {self.status} - {self.amount}"