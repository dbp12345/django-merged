from django.db import models

from exchange.models import Contacts_Prop


class Custom_Fields(models.Model):
    privser_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    main_field = models.BooleanField(default=False)
    privser_name = models.CharField(max_length=512, unique=False)  # MySQL may not allow unique CharFields to have a max_length > 255
    privser_fieldKey = models.CharField(max_length=512, blank=True, null=True)
    privser_placeholder = models.CharField(max_length=255, blank=True, null=True)
    privser_dataType = models.CharField(max_length=255, blank=True, null=True)
    exchange_property_name = models.CharField(max_length=255, blank=True, null=True)
    exchange_property = models.OneToOneField(Contacts_Prop, on_delete=models.SET_NULL, blank=True, null=True)
    no_sync = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Custom field"
        verbose_name_plural = "Custom fields"

    def updated_at_readable(self):
        return self.updated_at.strftime("%m-%d-%Y %H:%M:%S")

    def __str__(self):
        return self.privser_name or "-"
