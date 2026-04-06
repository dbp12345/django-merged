from django.db import models


class Contacts(models.Model):
    class StatusCode(models.IntegerChoices):
        NEW = 0, "New"
        IN_PROGRESS = 1, "In Progress"
        COMPLETED = 5, "Completed"
        CANCELED = 19, "Canceled"
        ERROR = 400, "Error"

    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=255, unique=True)
    contact_id = models.CharField(max_length=255, unique=True)
    changed_properties = models.JSONField(default=dict, blank=True, null=True)
    properties = models.JSONField(default=dict, blank=True, null=True)
    last_activity = models.DateTimeField(blank=True, null=True)
    date_updated = models.DateTimeField(blank=True, null=True)
    status_code = models.SmallIntegerField(choices=StatusCode, default=StatusCode.NEW)
    test = models.SmallIntegerField(default=0)
    modified_by = models.CharField(max_length=100, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        constraints = [
            models.UniqueConstraint(fields=["email", "contact_id"], name="unique_email_contact_privser")
        ]

    def updated_at_readable(self):
        return self.updated_at.strftime("%m-%d-%Y %H:%M:%S")

    # def save(self, *args, **kwargs):
    # if self.changed_properties and len(self.changed_properties) > 0:
    #     self.status_code = self.StatusCode.IN_PROGRESS
    # if self.pk:
    #     original = Contacts.objects.get(pk=self.pk)
    #     if original.changed_properties != self.changed_properties:
    #         self.status_code = self.StatusCode.IN_PROGRESS

    # super().save(*args, **kwargs)

    def __str__(self):
        return self.email if self.email is not None else ""
