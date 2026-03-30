from django.db import models
import uuid
from apps.common.models import TimeStampMixin
# Create your models here.


class ServiceRequest(TimeStampMixin):
    ''' Model representing a service request made by a user for a specific device, including details such as issue description, status, and resolution notes.'''

    class StatusChoices(models.TextChoices):
        PENDING = 'pending','Pending'
        VISIT_CHARGE_PENDING = 'visit_charge_pending','Visit Charge Pending'
        VISIT_CHARGE_PAID = 'visit_charge_paid','Visit Charge Paid'
        ASSIGNED = 'assigned','Assigned'
        IN_PROGRESS = 'in_progress','In Progress'
        QUOTE_SENT = 'quote_sent','Quote Sent'
        QUOTE_APPROVED = 'quote_approved','Quote Approved'
        QUOTE_PAYMENT_PENDING = 'quote_payment_pending',' Quote Payment Pending'
        QUOTE_PAYMENT_PAID = 'quote_payment_paid',' Quote Payment Paid'
        RESOLVED = 'resolved','Resolved'
        REJECTED = 'rejected','Rejected' 
        CLOSED = 'closed','Closed'

    class PriorityChoices(models.TextChoices):
        LOW = 'low','Low'
        MEDIUM = 'medium','Medium'
        HIGH = 'high','High'
        URGENT = 'urgent','Urgent'
    
    class TypeChoices(models.TextChoices):
        REPAIR = 'repair','Repair'
        MAINTENANCE = 'maintenance','Maintenance'
        INSTALLATION = 'installation','Installation'
        OTHER = 'other','Other'

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey('devices.Device', on_delete=models.CASCADE, related_name='service_requests')
    customer = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='service_requests')
    assigned_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_service_requests')
    issue_description = models.TextField()
    status = models.CharField(max_length=50, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    priority = models.CharField(max_length=20, choices=PriorityChoices.choices, default=PriorityChoices.MEDIUM)
    service_type = models.CharField(max_length=20, choices=TypeChoices.choices, default=TypeChoices.OTHER)
    resolution_notes = models.TextField(blank=True, null=True)
    visit_charge = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    parts_charge = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_charge = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_visit_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer','created_at']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['status']),
        ]



class ServiceRequestDocument(TimeStampMixin):
    '''Model representing files associated with a service request, allowing users to upload photos of the device issue for better diagnosis and resolution.'''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='service_request_document/')
    file_name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)



class ServiceRequestActivity(TimeStampMixin):
    '''Model representing the activity log for a service request, tracking status changes, comments, and timestamps for better transparency and communication between customers and service professionals.'''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.TextField(blank=True, null=True)
    from_status = models.CharField(max_length=50, blank=True, null=True)
    to_status = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']


