from urllib.parse import urlencode

from django.db import models

def default_columns():
    return ["Email", "job_title"]
class Saved_Filter(models.Model):
    name = models.CharField(max_length=255, unique=True)
    params = models.JSONField()
    order = models.IntegerField(default=0)
    columns = models.JSONField(default=default_columns)
    columns_main = models.JSONField(default=dict)
    dashboard = models.BooleanField(default=False)

    def __str__(self):
        return self.name or "-"

    def get_query_string(self):
        query_dict = []

        for f in self.params.get("str", []):
            query_dict.append(("field_str", f["field"]))
            query_dict.append(("filter_str", f["value"]))
            query_dict.append(("filter_operator", f["operator"]))

        for f in self.params.get("date", []):
            query_dict.append(("field_date", f["field"]))
            query_dict.append(("filter_from", f.get("from", "")))
            query_dict.append(("filter_to", f.get("to", "")))

        for f in self.params.get("relative", []):
            query_dict.append(("field_relative_date", f["field"]))
            query_dict.append(("relative_operator", f.get("operator", "")))
            query_dict.append(("relative_days", f.get("days", "")))

        return urlencode(query_dict, doseq=True)
