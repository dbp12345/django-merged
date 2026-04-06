from django.db import models

'''
{
    "metadata": {
        "contentItemCount": 63
    },
    "content": [
        {
            "payPeriodId": "1070080855174191",
            "intervalCode": "BI_WEEKLY",
            "status": "INITIAL",
            "description": "Bi-weekly Payroll (2)",
            "startDate": "2025-09-08T00:00:00Z",
            "endDate": "2025-09-21T00:00:00Z",
            "submitByDate": "2025-09-22T00:00:00Z",
            "checkDate": "2025-09-24T00:00:00Z",
            "checkCount": 0
        },
        {
            "payPeriodId": "1020053160696039",
            "status": "COMPLETED",
            "description": "Garcia Lopez",
            "startDate": "2025-09-03T00:00:00Z",
            "endDate": "2025-09-17T00:00:00Z",
            "submitByDate": "2025-09-17T00:00:00Z",
            "checkDate": "2025-09-19T00:00:00Z",
            "checkCount": 1
        }
    ],
    "links": [
        {
            "rel": "self",
            "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/payperiods?from=2025-05-12T00%3A00%3A00Z&to=2050-01-01T00%3A00%3A00Z?from=2025-05-12T00:00:00Z&to=2050-01-01T00:00:00Z"
        }
    ]

'''


class PayPeriod(models.Model):
    id = models.AutoField(primary_key=True)
    company_id = models.CharField(max_length=64, null=True, blank=True)
    payperiod_id = models.CharField(max_length=64, unique=True, db_index=True)
    interval_code = models.CharField(max_length=64, null=True, blank=True)
    status = models.CharField(max_length=64, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    submit_by_date = models.DateField(null=True, blank=True)
    check_date = models.DateField(null=True, blank=True)
    check_count = models.IntegerField(null=True, blank=True)
    raw_json = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "PayPeriod"
        verbose_name_plural = "PayPeriods"
        ordering = ("-start_date",)
        indexes = [
            models.Index(fields=["company_id", "start_date"]),
            models.Index(fields=["payperiod_id"]),
        ]

    def __str__(self):
        return f"{self.payperiod_id} / {self.description} ({self.start_date} — {self.end_date})"
