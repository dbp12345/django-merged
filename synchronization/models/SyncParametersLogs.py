from enum import Enum

from django.db import models

from company.models import Employees
from privser.models import Contacts as ContactsPrivser, Custom_Fields


class System(Enum):
    privser = "Privser"
    exchange = "Exchange"
    local = "Local"
    NA = "N/A"


class Sync_Parameters_Logs(models.Model):
    class StatusCode(models.IntegerChoices):
        NEW = 0, "Not Processed"
        IN_PROGRESS = 1, "Processing"
        # TEST = 100, "Test"
        COMPLETED = 5, "Sync Completed"
        IGNORE = 6, "Ignored"
        NO_CHANGES = 7, "No Data Changes"
        NO_RELATIONS = 9, "No Data Links"
        NO_CONTACT_LINK = 10, "No Contact Link"
        NO_PARAMETER_LINK = 11, "No Parameter Link"
        CANCELED = 19, "Canceled"
        ERROR = 400, "Processing Error"
        ERROR_API = 404, "External API Error"
        LOG = 50, "Log Entry"

    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=255, unique=False)
    employee = models.ForeignKey(
        Employees,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="sync_logs_employees"
    )
    contact_privser = models.ForeignKey(
        ContactsPrivser,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="sync_logs_privser"
    )
    privser_custom_fields = models.ForeignKey(
        Custom_Fields,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="sync_logs_parameters"
    )
    # contacts_prop = models.ForeignKey(
    #     Contacts_Prop,
    #     on_delete=models.SET_NULL,
    #     related_name="contacts_prop_entries",
    #     db_index=True,
    #     db_constraint=False,
    #     db_column="contacts_prop_id"
    # )
    property_name = models.CharField(max_length=255, blank=True, null=True)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    old_value_updated = models.DateTimeField(blank=True, null=True)
    new_value_updated = models.DateTimeField(blank=True, null=True)
    source_system = models.CharField(max_length=20, choices=[(s.name, s.value) for s in System])
    target_system = models.CharField(max_length=20, choices=[(s.name, s.value) for s in System])
    body = models.JSONField(default=dict, blank=True, null=True)
    removed = models.BooleanField(default=False)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    status_code = models.SmallIntegerField(choices=StatusCode, default=StatusCode.NEW)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sync_Parameters_Logs"
        verbose_name_plural = "Sync_Parameters_Logs"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["target_system"]),
            models.Index(fields=["updated_at"]),
        ]
