from django.db import models

'''
{
    "workerId": "004UWBZQLAT33HW8993C",
    "employeeId": "1416",
    "workerType": "EMPLOYEE",
    "exemptionType": "NON_EXEMPT",
    "workState": "OR",
    "birthDate": "1997-08-30T00:00:00Z",
    "sex": "NOT_SPECIFIED",
    "hireDate": "2021-07-21T00:00:00Z",
    "name": {
        "familyName": "Mendoza",
        "middleName": "E",
        "givenName": "Andres"
    },
    "legalId": {
        "legalIdType": "SSN",
        "legalIdValue": "625055640"
    },
    "laborAssignmentId": "1070061944834037",
    "locationId": "1060039934748789",
    "organization": {
        "organizationId": "1070061612875206",
        "name": "100 Firefighters",
        "number": "100"
    },
    "currentStatus": {
        "workerStatusId": "004UWBZQKMVOXG1R1SBV",
        "statusType": "TERMINATED",
        "statusReason": "LACK_OF_WORK___END_OF_SEASON",
        "effectiveDate": "2023-10-31T00:00:00Z"
    },
    "links": [
        {
            "rel": "self",
            "href": "https://api.paychex.com/workers/004UWBZQLAT33HW8993C"
        },
        {
            "rel": "communications",
            "href": "https://api.paychex.com/workers/004UWBZQLAT33HW8993C/communications"
        }
    ]
}

'''


class CompanyWorkers(models.Model):
    id = models.AutoField(primary_key=True)
    company_id = models.CharField(max_length=64, null=True, blank=True)
    worker_id = models.CharField("Worker Id", max_length=128, unique=True, db_index=True)
    employee_id = models.CharField("Employee Id", max_length=128, db_index=True, null=True, blank=True)
    worker_type = models.CharField("Worker Type", max_length=50, null=True, blank=True)
    exemption_type = models.CharField("Exemption Type", max_length=50, null=True, blank=True)
    work_state = models.CharField("State", max_length=10, null=True, blank=True)
    birth_date = models.DateField("BirthDate", null=True, blank=True)
    sex = models.CharField("Sex", max_length=50, null=True, blank=True)
    hire_date = models.DateField("Hire Date", null=True, blank=True)
    family_name = models.CharField("FamilyName", max_length=100, null=True, blank=True)
    middle_name = models.CharField("MiddleName", max_length=100, null=True, blank=True)
    given_name = models.CharField("GivenName", max_length=100, null=True, blank=True)
    legal_id_type = models.CharField("Legal Id Type", max_length=50, null=True, blank=True)
    legal_id_value = models.CharField("Legal Id Value", max_length=50, null=True, blank=True)
    labor_assignment_id = models.CharField("Labor Assignment Id", max_length=50, null=True, blank=True)
    location_id = models.CharField("Location Id", max_length=50, null=True, blank=True)
    organization_id = models.CharField("Organization id", max_length=50, null=True, blank=True)
    organization_name = models.CharField("oRganization name", max_length=128, null=True, blank=True)
    organization_number = models.CharField("Organization number", max_length=50, null=True, blank=True)
    worker_status_id = models.CharField("Worker Status Id", max_length=50, null=True, blank=True)
    status_type = models.CharField("Status Type", max_length=50, null=True, blank=True)
    status_reason = models.CharField("Status Reason", max_length=50, null=True, blank=True)
    status_effective_date = models.DateField("Status Effective Date", null=True, blank=True)
    raw_json = models.JSONField(null=True, blank=True)

    employees = models.ForeignKey(
        "company.Employees",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="company_workers_as_employees",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company Worker"
        verbose_name_plural = "Company Workers"
        indexes = [
            models.Index(fields=["worker_id"]),
            models.Index(fields=["employee_id"]),
        ]

    def __str__(self):
        return f"{self.given_name} {self.family_name}"
