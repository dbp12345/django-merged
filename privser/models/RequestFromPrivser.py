from django.db import models

class Request_From_Privser(models.Model):
    class StatusCode(models.IntegerChoices):
        NEW = 0, "New"
        IN_PROGRESS = 1, "In Progress"
        COMPLETED = 5, "Completed"
        IGNORE = 6, "Ignore"
        USER_NOT_FOUND = 9, "No Email in Exchange"
        CANCELED = 19, "Canceled"
        ERROR = 400, "Error"

    id = models.AutoField(primary_key=True)
    contacts = models.ForeignKey("company.Employees", on_delete=models.CASCADE, related_name="request_from_privser", blank=True, null=True)

    request = models.JSONField(default=dict)
    status_code = models.SmallIntegerField(choices=StatusCode, default=StatusCode.NEW)
    errors = models.JSONField(default=dict, blank=True, null=True)
    critical = models.JSONField(default=dict, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Request from Privser"
        verbose_name_plural = "Requests from Privser"

    def updated_at_readable(self):
        return self.updated.strftime("%m-%d-%Y %H:%M:%S")


    def __str__(self):
        # return self.email if self.email else "None"
        return self.email or "-"
