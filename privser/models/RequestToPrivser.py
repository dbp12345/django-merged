from django.db import models

from company.models import Employees


class Request_To_Privser(models.Model):
    class StatusCode(models.IntegerChoices):
        NEW = 0, "New"
        IN_PROGRESS = 1, "In Progress"
        COMPLETED = 5, "Completed"
        CANCELED = 19, "Canceled"
        EMAIL_ERRORS = 35, "EMAIL ERRORS"
        ERROR = 400, "Error"
        CRITICAL = 404, "Critical"

    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, related_name="request_to_privser_entries")

    # contacts_id = models.IntegerField()
    changed_properties = models.JSONField(default=dict, blank=True, null=True)
    response_privser = models.JSONField(default=dict, blank=True, null=True)
    status_code = models.SmallIntegerField(choices=StatusCode, default=StatusCode.NEW)
    errors = models.JSONField(default=dict, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Request"
        verbose_name_plural = "Requests"

    def updated_at_readable(self):
        return self.updated_at.strftime("%m-%d-%Y %H:%M:%S")

    def __str__(self):
        return self.employee.email if self.employee.email else "None"
        # return self.employees.email
