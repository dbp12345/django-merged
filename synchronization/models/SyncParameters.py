from django.db import models

from privser.models import Custom_Fields
from synchronization.models import Sync


class Sync_Parameters(models.Model):
    id = models.AutoField(primary_key=True)
    sync = models.ForeignKey(Sync, on_delete=models.CASCADE, related_name="sync_parameters")
    privser_custom_fields = models.ForeignKey(
        Custom_Fields,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="sync_parameters"
    )
    privser_value = models.TextField(blank=True, null=True)
    privser_datetime = models.DateTimeField(blank=True, null=True)
    privser_apply = models.BooleanField(default=False)
    exchange_value = models.TextField(blank=True, null=True)
    exchange_datetime = models.DateTimeField(blank=True, null=True)
    exchange_apply = models.BooleanField(default=False)
    exchange_property_not_found = models.CharField(max_length=255, blank=True, null=True)
    privser_property_not_found = models.CharField(max_length=255, blank=True, null=True)
    override_value = models.TextField(blank=True, null=True)
    body = models.JSONField(default=dict, blank=True, null=True)
    removed = models.BooleanField(default=False)


    # @property
    # def related_exchange_property(self):
    #     if self.privser_custom_fields:
    #         return self.privser_custom_fields.exchange_property
    #     return None

    def __str__(self):
        return ""

    class Meta:
        verbose_name = "Awaiting Review"
        verbose_name_plural = "Awaiting Review"

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = Sync_Parameters.objects.get(pk=self.pk)
            if old_instance.removed and not self.removed:
                self.privser_apply = False
                self.exchange_apply = False

        super().save(*args, **kwargs)

class ChangesInParameter(Sync_Parameters):
    class Meta:
        proxy = True
        verbose_name = "Approved Parameters"
        verbose_name_plural = "Approved Parameters"