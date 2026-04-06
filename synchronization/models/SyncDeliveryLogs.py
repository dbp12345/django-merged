from django.db import models

from company.models import Employees
from exchange.models import Contacts_Prop
from privser.models import Custom_Fields

class Sync_Delivery_Logs(models.Model):
    class StatusCode(models.TextChoices):
        NEW = "New", "New"
        NOT_PROCESSED = "Not Processed", "Not Processed"
        PROCESSING = "Processing", "Processing"
        SYNC_COMPLETED = "Sync Completed", "Sync Completed"
        IGNORED = "Ignored", "Ignored"
        NO_DATA_CHANGES = "No Data Changes", "No Data Changes"
        NO_DATA_LINKS = "No Data Links", "No Data Links"
        NO_CONTACT_LINK = "No Contact Link", "No Contact Link"
        MULTIPLE_CONTACT_LINK = "Multiple Contact Link", "Multiple Contact Link"
        NO_PARAMETER_LINK = "No Parameter Link", "No Parameter Link"
        CANCELED = "Canceled", "Canceled"
        PROCESSING_ERROR = "Processing Error", "Processing Error"
        EXTERNAL_API_ERROR = "External API Error", "External API Error"
        LOG_ENTRY = "Log Entry", "Log Entry"

    class TargetSystemChoices(models.TextChoices):
        PRIVSER = "Privser", "Privser"
        EXCHANGE = "Exchange", "Exchange"
        LOCAL = "Local", "Local"
        NA = "N/A", "N/A"

    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=255, unique=False)
    employee = models.ForeignKey(
        Employees,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="sync_delivery_logs_employees"
    )
    contacts_prop = models.ForeignKey(
        Contacts_Prop,
        on_delete=models.SET_NULL,
        related_name="sync_delivery_logs_entries",
        db_index=True,
        db_constraint=False,
        db_column="contacts_prop_id",
        blank=True, null=True
    )
    privser_custom_fields = models.ForeignKey(
        Custom_Fields,
        on_delete=models.SET_NULL,
        related_name="sync_delivery_logs_parameters",
        blank=True, null=True
    )
    contacts_prop_name = models.CharField(max_length=255, blank=True, null=True)
    privser_custom_fields_name = models.CharField(max_length=512, blank=True, null=True)
    # privser_custom_fields_main_field = models.
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    target_system = models.CharField(
        max_length=20,
        choices=TargetSystemChoices.choices,
        default=TargetSystemChoices.NA
    )
    body = models.JSONField(default=dict, blank=True, null=True)
    removed = models.BooleanField(default=False)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    status_code = models.CharField(
        max_length=50,
        choices=StatusCode.choices,
        default=StatusCode.NEW
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name = "Sync Delivery Log"
        verbose_name_plural = "Sync Delivery Logs"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["target_system"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self):
        return f"[{self.email}] {self.contacts_prop_name or self.privser_custom_fields_name or 'Unknown'}"

    def save(self, *args, **kwargs):
        if self.body is None:
            self.body = {}
        super().save(*args, **kwargs)
