from django.db import models


class Contacts_Prop_Logs(models.Model):
    class StatusCode(models.IntegerChoices):
        NEW = 0, "NEW"
        FIELD_WAS_NOT_UPDATED = 1, "FIELD NOT UPDATED"
        SAVE = 5, "SAVE"
        IGNORE = 6, "Ignore"
        USER_NOT_FOUND = 9, "No Email in Exchange"
        CRITICAL = 50, "CRITICAL"

    id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=255)
    # request_to_exchange = models.ForeignKey("exchange.Request_To_Exchange", on_delete=models.CASCADE, related_name="prop_logs")
    # request_to_exchange_id = models.IntegerField(blank=True, null=True)
    body = models.JSONField(default=dict, blank=True, null=True)
    critical = models.JSONField(default=dict, blank=True, null=True)
    status_code = models.SmallIntegerField(choices=StatusCode, default=StatusCode.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "_logs"
        verbose_name_plural = "_logs"

    def updated_at_readable(self):
        return self.updated_at.strftime("%m-%d-%Y %H:%M:%S")

    def __str__(self):
        return self.email or "-"
