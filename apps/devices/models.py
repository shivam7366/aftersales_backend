from django.db import models
import uuid

from apps.common.models import TimeStampMixin

# Create your models here.


class Device(TimeStampMixin):
    '''Model representing a device registered by a user, including details such as name, model, serial number, and purchase date.'''
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='devices')
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    model_number = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    purchase_date = models.DateField()



    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user','created_at']),
            models.Index(fields=['brand']),
        ]
    def __str__(self):
        return f"{self.name} ({self.model_number}) - {self.user.email}"
    