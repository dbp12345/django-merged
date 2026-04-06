from django.db import models

from core.utils import model_directory_path


class Company(models.Model):
    name = models.CharField(
        max_length=255, blank=False, null=False, verbose_name="Name"
    )
    address = models.CharField(
        max_length=512, blank=True, null=True, verbose_name="Address"
    )
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Phone")
    dot = models.CharField(max_length=100, blank=True, null=True, verbose_name="DOT")
    tax = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tax ID")
    mspa = models.CharField(max_length=100, blank=True, null=True, verbose_name="MSPA")
    email = models.EmailField(
        max_length=100, blank=True, null=True, verbose_name="Email"
    )
    articles_of_organization_file = models.ImageField(
        upload_to=model_directory_path,
        blank=True,
        null=True,
        verbose_name="Articles of Organization",
    )
    mspa_license_file = models.ImageField(
        upload_to=model_directory_path,
        blank=True,
        null=True,
        verbose_name="MSPA License",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
