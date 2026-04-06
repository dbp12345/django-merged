from django.db import models
from django.conf import settings
from django.utils import timezone

class EventType(models.TextChoices):
    CLOCK_IN = "Clocked In", "Clock In"
    CLOCK_OUT = "Clocked Out", "Clock Out"
    # MEAL_START = "MEAL_START", "Meal Start"
    # MEAL_END = "MEAL_END", "Meal End"
    # BREAK_START = "BREAK_START", "Break Start"
    # BREAK_END = "BREAK_END", "Break End"
    # SHIFT_START = "SHIFT_START", "Shift Start"
    # SHIFT_END = "SHIFT_END", "Shift End"
    # ADJUSTMENT = "ADJUSTMENT", "Adjustment"
    # AUTO_CLOCK_OUT = "AUTO_CLOCK_OUT", "Auto Clock Out"
    # UNKNOWN = "UNKNOWN", "Unknown"


class Punch_Event(models.Model):
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
        related_name="punch_events",
        verbose_name="User",
        db_index=True,
    )
    event_type = models.CharField(max_length=32, choices=EventType.choices, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    source = models.CharField(max_length=64, blank=True, null=True)
    is_correction = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["employee", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} — {self.timestamp} — {self.user or self.employee or 'unknown'}"

