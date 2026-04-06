from django.conf import settings
from django.db import models


class Work_Session(models.Model):
    employee = models.ForeignKey(
        "company.Employees",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Employee",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="work_sessions",
        verbose_name="User",
        db_index=True,
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)  # NULL = открытая сессия
    duration_seconds = models.IntegerField(null=True, blank=True)
    created_from_punches = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["user", "start_time"]),
            models.Index(fields=["employee", "start_time"]),
        ]

    def __str__(self):
        return f"{self.employee or self.user} {self.start_time} → {self.end_time or 'open'}"
