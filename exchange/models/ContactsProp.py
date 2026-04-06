from django.db import models

class Contacts_Prop(models.Model):
    class TypeChoices(models.TextChoices):
        STRING = "String", "String"
        SYSTEM_TIME = "SystemTime", "SystemTime"
        DOUBLE = "Double", "Double"
        BOOL = "Bool", "Bool"
        DOCUMENT = "Document", "Document"
        ARRAY = "Array", "Array"

    id = models.AutoField(primary_key=True)
    property_name = models.CharField(max_length=255, unique=True)
    property_type = models.CharField(choices=TypeChoices.choices, max_length=50, blank=True, null=True)
    property_tag = models.CharField(max_length=50, blank=True, null=True)
    property_set_id = models.CharField(max_length=100, blank=True, null=True)
    datetime_format = models.CharField(max_length=50, blank=True, null=True)
    visibility = models.BooleanField(default=False)
    param_mirror = models.BooleanField(default=False) # скрываем, так как он используется как обьект-параметр
    updated_at = models.DateTimeField(auto_now=True)

    # def get_property_for_ews(self):
    #     string_fields = {field.name: getattr(self, field.name) for field in self._meta.fields if
    #                      self.visibility == True}
    #
    #     return json.dumps(string_fields, ensure_ascii=False, indent=4)

    # def to_json(self):
    #     string_fields = {field.name: getattr(self, field.name) for field in self._meta.fields if
    #                      isinstance(field, (models.CharField, models.TextField))}
    #
    #     return json.dumps(string_fields, ensure_ascii=False, indent=4)

    def __str__(self):
        return self.property_name or "-"
        # return self.to_json()

    class Meta:
        verbose_name = "Property"
        verbose_name_plural = "Properties"
    """
    def __str__(self):
        # return json.dumps(self.properties, ensure_ascii=False)
        return f"{self.property_name}: {self.property_value}"
    """