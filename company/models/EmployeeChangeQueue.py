from django.db import models

from company.models import Employees
from exchange.models import Contacts_Prop


class Employee_Change_Queue(models.Model):
    class StatusCode(models.IntegerChoices):
        NEW = 0, "New"
        CANCELED = 19, "Canceled"
        COMPLETED = 5, "Completed"
        IN_PROGRESS = 1, "In Progress"
        ERROR = 400, "Error"

    employee = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        related_name="change_queue_entries",
        db_index=True,
        db_constraint=False,
        db_column="employees_id"
    )
    contacts_prop = models.ForeignKey(
        Contacts_Prop,
        on_delete=models.CASCADE,
        related_name="change_queue_entries",
        db_index=True,
        db_constraint=False,
        db_column="contacts_prop_id"
    )
    new_value = models.CharField(max_length=512, blank=True, null=True, db_index=True)
    new_value_date = models.DateTimeField(blank=True, null=True)
    status = models.SmallIntegerField(choices=StatusCode, default=StatusCode.NEW)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee_id} / {self.contacts_prop.property_name} -> {self.new_value}"

    class Meta:
        verbose_name = "Change Queue"
        verbose_name_plural = "Change Queue"
