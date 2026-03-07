from django.db import models



class TimeStampMixin(models.Model):
    '''Abstract base class that provides created_at and updated_at fields for timestamping model instances.'''
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True