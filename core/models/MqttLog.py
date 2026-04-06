from django.db import models

STATUS = [
    ("Ok", "Ok"),
    ("Pending", "Pending"),
    ("Failed", "Failed"),
]

class Mqtt_Log(models.Model):
    topic = models.CharField(max_length=100, default=None, blank=True, null=True)
    raw_data = models.TextField()
    parsed_data = models.JSONField(blank=True, null=True)
    condition_content = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS, default="Pending")
    error = models.TextField(blank=True, null=True)
    raw_timestamp = models.BigIntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    phone = models.CharField(max_length=50, default=None, blank=True, null=True)
    beacon = models.CharField(max_length=50, default=None, blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
