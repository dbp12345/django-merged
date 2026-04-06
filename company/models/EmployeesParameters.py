from django.db import models

from company.models.Employees import Employees
from core.utils import model_directory_path_property
from exchange.models import Contacts_Prop


class Employees_Parameters(models.Model):
    employee = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        related_name="employees_parameters_entries",
        db_index=True,
        db_constraint=False,
        db_column="employees_id"
    )
    contacts_prop = models.ForeignKey(
        Contacts_Prop,
        on_delete=models.CASCADE,
        related_name="contacts_prop_entries",
        db_index=True,
        db_constraint=False,
        db_column="contacts_prop_id"
    )
    value = models.CharField(max_length=512, blank=True, null=True, db_index=True)
    # value_long = models.TextField(blank=True, null=True) # То что не поместилось в value
    value_date = models.DateTimeField(blank=True, null=True)
    value_file = models.FileField(upload_to=model_directory_path_property, blank=True, null=True)
    value_bool = models.BooleanField(default=False)
    value_array = models.JSONField(default=list)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    sync_updated_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return ""

    class Meta:
        verbose_name = "Parameters"
        verbose_name_plural = "Parameters"
        indexes = [
            models.Index(fields=["employee", "contacts_prop", "updated_at"])
        ]
        constraints = [
            models.UniqueConstraint(fields=["employee", "contacts_prop"], name="unique_employee_param")
        ]
    # Transferring this into signals
    # def save(self, *args, **kwargs):
    #     if self.contacts_prop.property_type == Contacts_Prop.TypeChoices.SYSTEM_TIME and self.value:
    #         # try:
    #         datetime_format = self.contacts_prop.datetime_format
    #         parsed_date = datetime.strptime(self.value, datetime_format)
    #         self.value_date = parsed_date
    #         # except (ValueError, TypeError):
    #         #     print("___ERROR___")
    #         #     print(self.contacts_prop.property_name, self.value)
    #         #     self.value_date = None  # Если вдруг кривая дата или пустое значение
    #
    #     else:
    #         self.value_date = None  # If it is not a date, we always reset it.
    #
    #     super().save(*args, **kwargs)
