from enum import Enum

from django.db import models
from django.contrib.auth.models import User as DjangoAdminUser


class Type(Enum):
    EMPLOYEES_AJAX = "Employees table"
    CREWS_ZONES_MODAL = "Crews zone (modal)"


class Fields_Settings(models.Model):
    user = models.ForeignKey(DjangoAdminUser, on_delete=models.CASCADE)
    fields = models.JSONField()
    type = models.CharField(
        max_length=25,
        choices=[(type.name, type.value) for type in Type],
        default=None,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.user.username or "-"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "type"], name="unique_user_type")
        ]
