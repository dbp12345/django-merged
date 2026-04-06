# from django.core.exceptions import ValidationError
from django.db import models
from core.utils import model_directory_path


class ContractType(models.TextChoices):
    ENGINE = "Engine", "Engine"
    CREW = "Crew", "Crew"


# TO-DO больше не юзаем. Сделали в бд
class Company(models.TextChoices):
    DUST_BUSTERS_PLUS_LLC = "Dust Busters Plus LLC", "Dust Busters Plus LLC"
    IDAHO_LAND_SERVICES_LLC = "Idaho Land Services LLC", "Idaho Land Services LLC"
    DBP_SOUTH_LLC = "DBP South LLC", "DBP South LLC"
    SOUTHERN_SOLUTIONS_LLC = "Southern Solutions LLC", "Southern Solutions LLC"


class Contracts(models.Model):
    # dispatch = models.OneToOneField(Dispatch, null=True, on_delete=models.SET_NULL, verbose_name="Dispatch")
    # dispatch = models.ManyToManyField(Dispatch, blank=True, verbose_name="Dispatches")
    # firecrew = models.OneToOneField("company.FireCrew", blank=True, unique=False, null=True, on_delete=models.SET_NULL, verbose_name="Crew")
    truck = models.ForeignKey("dispatch.Truck", blank=True, null=True, on_delete=models.SET_NULL, related_name="contracts_entries", verbose_name="Truck")

    crew_boss_primary = models.ForeignKey(
        "company.Employees",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contracts_as_primary_entries",
        verbose_name="Crew Boss Primary"
    )

    crew_boss_alternate = models.ForeignKey(
        "company.Employees",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contracts_as_alternate_entries",
        verbose_name="Crew Boss Alternate #1"
    )

    crew_boss_alternate_2 = models.ForeignKey(
        "company.Employees",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contracts_as_alternate_2_entries",
        verbose_name="Crew Boss Alternate #2"
    )

    number = models.CharField(max_length=100, blank=False, null=False, unique=False, verbose_name="Contract number")
    award_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Award Number")
    resource_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Resource Number")
    type_category = models.CharField(
        max_length=25,
        choices=ContractType.choices,
        blank=True,
        null=True,
        editable=True,
        verbose_name="Type category"
    )
    type_number = models.IntegerField(blank=True, null=True, verbose_name="Type number")
    dispatch_address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dispatch address")
    region = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Region")
    agency = models.CharField(max_length=100, blank=True, null=True, verbose_name="Agency")
    rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Rate")
    per_dof_hr = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="$ per DOF HR"
    )
    expiration_date = models.DateField(blank=True, null=True, verbose_name="Expiration date")

    award_sheet_file = models.FileField(upload_to=model_directory_path, blank=True, null=True, verbose_name="Award sheet file")
    full_contract = models.FileField(upload_to=model_directory_path, blank=True, null=True, verbose_name="Full Contract")

    company = models.CharField(
        max_length=25,
        choices=Company.choices,
        blank=True,
        null=True,
        editable=True,
        verbose_name="Company"
    )

    company_rel = models.ForeignKey(
        "company.Company",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="contracts_entries",
        verbose_name="Company"
    )

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # def clean(self):
    #     if bool(self.firecrew) == bool(self.truck):
    #         raise ValidationError("Please specify either Crew or Truck, but not both.")

    # def save(self, *args, **kwargs):
    #     if self.firecrew and not self.truck:
    #         self.type_category = ContractType.CREW
    #     elif self.truck and not self.firecrew:
    #         self.type_category = ContractType.ENGINE
    #     super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Contract"
        verbose_name_plural = "Contracts"

    def __str__(self):
        parts = []
        if self.truck:
            parts.append(self.truck.vin_number or "")
        if self.resource_number:
            parts.append(self.resource_number)
        if self.type_category:
            parts.append(self.type_category)
        if self.type_number:
            parts.append(f"Type {self.type_number}")
        if self.agency:
            parts.append(self.agency)
        if self.region:
            parts.append(str(self.region))
        return ", ".join(parts)
