from django.db import models


class TimePunch(models.Model):
    # basic identity
    emp_identifier = models.CharField("EmpIdentifier", max_length=64, db_index=True)

    # external dedupe key (constructed from slice id or hash)
    external_id = models.CharField("External ID", max_length=128)

    first_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True)

    # times (store timezone-aware datetimes)
    apply_to_date = models.DateField("ApplyToDate", null=True, blank=True)

    in_time = models.DateTimeField("InTime", null=True, blank=True)
    in_time_actual = models.DateTimeField("InTimeActual", null=True, blank=True)
    out_time = models.DateTimeField("OutTime", null=True, blank=True)
    out_time_actual = models.DateTimeField("OutTimeActual", null=True, blank=True)

    # numeric slice ids
    in_time_slice_preid = models.IntegerField("InTimeSlicePreID", null=True, blank=True)
    out_time_slice_preid = models.IntegerField("OutTimeSlicePreID", null=True, blank=True)

    # location
    in_latitude = models.FloatField("InLatitude", null=True, blank=True)
    in_longitude = models.FloatField("InLongitude", null=True, blank=True)
    out_latitude = models.FloatField("OutLatitude", null=True, blank=True)
    out_longitude = models.FloatField("OutLongitude", null=True, blank=True)

    # meta
    in_type = models.CharField("InType", max_length=64, null=True, blank=True)
    out_type = models.CharField("OutType", max_length=64, null=True, blank=True)

    pay_type_id = models.IntegerField("PayTypeID", null=True, blank=True)
    pay_type_name = models.CharField("PayTypeName", max_length=255, null=True, blank=True)
    pay_type_code = models.CharField("PayTypeCode", max_length=64, null=True, blank=True)

    regular_minutes = models.IntegerField("RegularMinutes", null=True, blank=True)
    unpaid_minutes = models.IntegerField("UnpaidMinutes", null=True, blank=True)

    # complex / variable structures
    ot_info = models.JSONField("OTInfo", default=list, blank=True)
    labor_levels = models.JSONField("LaborLevels", default=dict, blank=True)

    # original fields that may exist
    in_clock_id = models.CharField("InClockID", max_length=128, null=True, blank=True)
    out_clock_id = models.CharField("OutClockID", max_length=128, null=True, blank=True)

    export_code = models.CharField(max_length=255, blank=True, null=True)

    # raw payload for audit/debug
    raw = models.JSONField("RawResponse", null=True, blank=True)

    row_hash = models.CharField(max_length=64, unique=True, db_index=True)  # prevents duplicates

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Time Punch"
        verbose_name_plural = "Time Punches"
        unique_together = (("emp_identifier", "external_id"),)
        ordering = ("-in_time",)
        indexes = [
            models.Index(fields=["emp_identifier", "apply_to_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.emp_identifier} @ {self.apply_to_date} in={self.in_time} out={self.out_time}"
