from enum import Enum

from django.db import models

class ApiType(Enum):
    PRIVSER = "Privser"
    EXCHANGE = "Exchange"
    PAYCHEX = "Paychex"

class Employee_Last_Updates(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.CharField(
        max_length=50,
        choices=[(type.name, type.value) for type in ApiType],
        default=None,
        blank=True,
        null=True
    )
    contact_id = models.CharField(max_length=255)
    date_updated = models.DateTimeField(blank=True, null=True)
    date_updated_str = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.id or "-"
