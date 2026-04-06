from django.db import models


class Paycheck(models.Model):
    paycheck_id = models.CharField(max_length=128, unique=True, db_index=True)
    company_id = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    payperiod_id = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    worker_id = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    paychex_worker = models.ForeignKey("paychex.CompanyWorkers", on_delete=models.SET_NULL, null=True, blank=True)
    check_date = models.DateField(null=True, blank=True, db_index=True)
    check_number = models.CharField(max_length=64, null=True, blank=True)   # из ответа: checkNumber
    check_type = models.CharField(max_length=64, null=True, blank=True)     # из ответа: checkType
    gross = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    net = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    raw_json = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["company_id"]),
            models.Index(fields=["payperiod_id"]),
            models.Index(fields=["worker_id"]),
            models.Index(fields=["check_date"]),
        ]

    def __str__(self):
        return f"{self.paycheck_id} ({self.check_date})"


class PaycheckComponent(models.Model):
    COMPONENT_TYPES = (
        ("EARNING", "Earning"),
        ("DEDUCTION", "Deduction"),
        ("TAX", "Tax"),
        ("OTHER", "Other"),
    )

    paycheck = models.ForeignKey(Paycheck, on_delete=models.CASCADE, related_name="components")
    component_id = models.CharField(max_length=64, null=True, blank=True)         # componentId из API
    check_component_id = models.CharField(max_length=64, null=True, blank=True)   # checkComponentId из API
    name = models.CharField(max_length=255, null=True, blank=True)
    component_type = models.CharField(max_length=32, choices=COMPONENT_TYPES, null=True, blank=True)
    classification_type = models.CharField(max_length=64, null=True, blank=True)  # classificationType
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    rate = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    hours = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    labor_assignment_id = models.CharField(max_length=64, null=True, blank=True)
    organization_id = models.CharField(max_length=64, null=True, blank=True)
    organization_name = models.CharField(max_length=128, null=True, blank=True)
    raw_json = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["component_id"]),
            models.Index(fields=["check_component_id"]),
            models.Index(fields=["component_type"]),
        ]

    def __str__(self):
        return f"{self.name or 'component'} ({self.amount or ''})"
