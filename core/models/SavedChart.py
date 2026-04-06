from django.db import models

DATA_TYPE = [("data", "data"), ("cumulative", "cumulative")]

class Saved_Chart(models.Model):
    name = models.CharField(max_length=255)
    course_id = models.IntegerField(null=True, blank=True)
    data_type = models.CharField(max_length=10, choices=DATA_TYPE, default="data")
    year_from = models.IntegerField(null=True, blank=True)
    year_to = models.IntegerField(null=True, blank=True)
    chart_type = models.CharField(max_length=10, choices=[("line", "Line"), ("bar", "Bar")], default="line")
    display_order = models.IntegerField(default=0)
    dashboard = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.display_order}. {self.name} ({self.year_from}-{self.year_to})"

    class Meta:
        ordering = ["display_order"]
