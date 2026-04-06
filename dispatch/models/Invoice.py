# from django.core.exceptions import ValidationError
from django.db import models
from core.utils import model_directory_path


# class Company(models.TextChoices):
#     DUST_BUSTERS_PLUS_LLC = "Dust Busters Plus LLC", "Dust Busters Plus LLC"
#     IDAHO_LAND_SERVICES_LLC = "Idaho Land Services LLC", "Idaho Land Services LLC"
#     DBP_SOUTH_LLC = "DBP South LLC", "DBP South LLC"
#     SOUTHERN_SOLUTIONS_LLC = "Southern Solutions LLC", "Southern Solutions LLC"


class Status(models.TextChoices):
    PAID = "Paid", "Paid"
    PAID_CHECK_IN_THE_MAIL = "Paid-Check in the mail", "Paid-Check in the mail"
    APPROVED_FOR_PAYMENT = "Approved for payment", "Approved for payment"
    READY_FOR_APPROVAL = "Ready for approval", "Ready for approval"
    IN_PROGRESS = "In progress", "In progress"
    WAITING_FOR_FINAL_INVOICE = "Waiting for Final Invoice", "Waiting for Final Invoice"
    CANCELED = "Canceled", "Canceled"
    MISSING = "Missing", "Missing"
    IRA_CREWS = "IRA Crews", "IRA Crews"


class Invoice(models.Model):
    dispatch = models.ForeignKey("dispatch.Dispatch", on_delete=models.CASCADE, related_name="invoices_entries", verbose_name="Dispatch")
    # company = models.CharField(max_length=100, choices=Company.choices, blank=True, null=True, verbose_name="Company")  # From Dispatch

    invoice_date = models.DateField(blank=True, null=True, verbose_name="Invoice Date")
    status = models.CharField(max_length=100, choices=Status.choices, blank=True, null=True, verbose_name="Status")
    # fire_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fire Name")  # From Fire object
    # ec_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="E/C Number")  # From Dispatch
    # incident_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Incident Number")  # From Fire object

    start_date = models.DateField(blank=True, null=True, verbose_name="Start Date")  # Crew Fire Run
    finish_date = models.DateField(blank=True, null=True, verbose_name="Finish Date")  # Crew Fire Run

    number_of_days = models.PositiveIntegerField(blank=True, null=True, verbose_name="Number Of Days")  # По желанию можешь делать auto-calc на админке

    invoice_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Invoice Amount")
    # crew = models.ForeignKey(
    #     "Crew",
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="invoices_as_crew_entries"
    # )
    # fire_crew = models.ForeignKey(
    #     "FireCrew",
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="invoices_as_fire_crew_entries"
    # )
    # crew_boss_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Crew Boss Name")  # From Dispatch

    invoice_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Invoice Number")
    date_paid = models.DateField(blank=True, null=True, verbose_name="Date Paid")
    check_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Check Amount")
    change_in_payment = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Change in Payment")

    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    file = models.FileField(upload_to=model_directory_path, blank=True, null=True, verbose_name="File")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"

    def __str__(self):
        return self.invoice_number or "-"
