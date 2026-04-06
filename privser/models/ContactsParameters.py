from django.db import models
from django.db.models import Q
from django.utils.functional import cached_property

from privser.models.Contacts import Contacts
from privser.models.CustomFields import Custom_Fields


class Contacts_Parameters(models.Model):
    contacts = models.ForeignKey(Contacts, on_delete=models.CASCADE, related_name="parameters")
    contacts_parameters = models.OneToOneField(
        Custom_Fields, on_delete=models.CASCADE, blank=True, null=True, related_name='parameters_custom_fields'
    )
    name = models.CharField(max_length=255, blank=True, null=True) # тут name сложно убрать, апи присылает ключи как строки и каждый искать долго в таблице для поиска id и привязки
    value = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    @cached_property
    def custom_fields_privser_name(self):
        custom_fields_obj = list(
            Custom_Fields.objects.filter(
                Q(privser_id=self.name) | Q(privser_name=self.name)
            )
        )
        if not custom_fields_obj:
            return "None obj"
        elif len(custom_fields_obj) > 1:
            return "Multi obj"
        else:
            custom_fields_obj_first = custom_fields_obj[0]
        return custom_fields_obj_first.privser_name

    def __str__(self):
        return f"{self.name} = {self.value}"

    class Meta:
        verbose_name = "Parameters"
        verbose_name_plural = "Parameters"