from django.db import models
from jobs.models import Job


class Invoice(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]

    job = models.OneToOneField(
        Job,
        on_delete=models.PROTECT,
        related_name="invoice",
    )

    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True)

    invoice_pdf = models.FileField(
        upload_to="invoices/pdfs/",
        null=True,
        blank=True,
        help_text="Uploaded or generated PDF for this invoice.",
    )

    # 🔹 NEW FIELDS
    date = models.DateField(null=True, blank=True)
    text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def company(self):
        return self.job.company

    @property
    def customer(self):
        return self.job.customer

    def __str__(self):
        return f"Invoice {self.invoice_number}"
