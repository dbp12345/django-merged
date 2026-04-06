from django.db import models
from django.contrib.auth.models import User

from core.utils import model_directory_path
from company.models.Employees import get_document_preview


class BankTransaction(models.Model):
    class BankNameChoices(models.TextChoices):
        CHASE_BANK = "Chase Bank", "Chase Bank"
        COLUMBIA_BANK = "Columbia Bank", "Columbia Bank"
        AMERICAN_EXPRESS = "American Express", "American Express"

    id = models.AutoField(primary_key=True)
    # date = models.DateField(verbose_name="Date")
    # time = models.TimeField(blank=True, null=True, verbose_name="Time")
    datetime = models.DateTimeField(blank=True, null=True, verbose_name="Datetime")
    bank_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bank #")
    bank_name = models.CharField(
        max_length=100,
        choices=BankNameChoices.choices,
        blank=True,
        null=True,
        verbose_name="Bank Name"
    )
    account_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Account Number")
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Amount"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="User"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Type")
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name="Category")
    project_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="Project Code")
    fixed_variable = models.BooleanField(default=False, verbose_name="Fixed/Variable")
    required_discretionary = models.BooleanField(default=False, verbose_name="Required/Discretionary")
    approved = models.BooleanField(default=False, verbose_name="Approved")
    growth = models.BooleanField(default=False, verbose_name="Growth")
    file = models.FileField(
        upload_to=model_directory_path,
        blank=True,
        null=True,
        verbose_name="File"
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bank Transaction"
        verbose_name_plural = "Bank Transactions"
        ordering = ("-datetime", "-updated_at")
        indexes = [
            models.Index(fields=["datetime", "bank_name"]),
            models.Index(fields=["user", "datetime"]),
        ]

    def __str__(self):
        parts = []
        if self.datetime:
            parts.append(f"Date: {self.datetime}")
        if self.bank_name:
            parts.append(f"Bank: {self.bank_name}")
        if self.amount is not None:
            parts.append(f"Amount: ${self.amount:,.2f}")
        return ", ".join(parts) if parts else f"Transaction #{self.id}"

    def file_preview(self):
        return get_document_preview(self.file)
