from django.db import models
from companies.models import Company
from contacts.models import Contact


class Job(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='jobs'
    )

    customer = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,
        related_name='jobs'
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    job_site_form = models.FileField(
        upload_to="jobs/site_forms/",
        null=True,
        blank=True,
        help_text="Uploaded or generated job site form PDF.",
    )

    # 🔹 NEW FIELDS
    date = models.DateField(null=True, blank=True)
    text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.customer})"
