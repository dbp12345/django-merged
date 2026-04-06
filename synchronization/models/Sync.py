from django.db import models

from company.models import Employees
from privser.models import Contacts as ContactsPrivser


class Sync(models.Model):
    class StatusCode(models.IntegerChoices):
        NEW = 0, "Not processed"
        IN_PROGRESS = 1, "In Progress"
        COMPLETED = 5, "Completed"
        IGNORE = 6, "Ignore"
        NO_CHANGES = 7, "No Changes"
        USER_NOT_FOUND = 9, "No Email in Exchange"
        CANCELED = 19, "Canceled"
        ERROR = 400, "Error"

    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=255, unique=True)
    contact_privser = models.ForeignKey(
        ContactsPrivser,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="sync_privser"
    )
    employee = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="sync_employees"
    )
    status_code = models.SmallIntegerField(choices=StatusCode, default=StatusCode.NEW)
    test = models.SmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email if self.email is not None else ""

    class Meta:
        verbose_name = "Sync"
        verbose_name_plural = "Sync"

    def get_active_parameters(self):
        return self.sync_parameters.filter(removed=False)

    # def update_status(self):
    #     from synchronization.services.SyncService import SyncService
    #     self.status_code = SyncService.get_correct_status(self)

    # def update_remote_contacts(self):
    #     from synchronization.services.SyncService import SyncService
    #     SyncService.update_remote_contacts(self)

    # def save(self, *args, **kwargs):
    #     # additional_actions = kwargs.pop('additional_actions', True)
    #     self.update_status()
    #     super().save(*args, **kwargs)
    #     # if additional_actions:
    #     #     from synchronization.services.SyncService import SyncService
    #     #     SyncService.update_remote_contacts(self)
