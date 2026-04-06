from enum import Enum

from django.db import models

class Status(Enum):
    OK = "Ok"
    PENDING = "Pending"
    FAILED = "Failed"

class Import_Dayonfire_Row(models.Model):
    job = models.CharField(max_length=50, default=None, blank=True, null=True)
    raw_data = models.JSONField()
    status = models.CharField(max_length=20, choices=[(status.name, status.value) for status in Status], default=None)
    error = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
