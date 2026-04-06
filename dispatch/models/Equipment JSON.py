from django.db import models
from django_jsonform.models.fields import JSONField

from dispatch.models.Dispatch import Equipment_group


class EquipmentType(models.Model):
    """Equipment type with its parameters"""

    name = models.CharField("Type Name", max_length=100)
    description = models.TextField("Description", blank=True)

    # Parameter schema for this equipment type
    parameters_schema = JSONField(
        "Parameter Schema",
        schema={
            "type": "array",
            "items": {
                "type": "object",
                "keys": {
                    "name": {
                        "type": "string",
                        "title": "Parameter Name",
                        "help_text": "For example: voltage, power, speed (in Latin, without spaces)",
                    },
                    "field_type": {
                        "type": "string",
                        "title": "Field Type",
                        "choices": ["string", "number", "boolean", "select", "date"],
                    },
                    "unit": {
                        "type": "string",
                        "title": "Unit of Measurement",
                        "help_text": "For example: V, kW, m/s (optional)",
                    },
                    "required": {"type": "boolean", "title": "Required Field"},
                    "choices": {
                        "type": "array",
                        "title": "Choice Options (for select only)",
                        "items": {"type": "string"},
                    },
                },
            },
        },
        default=list,
        blank=True,
    )

    class Meta:
        verbose_name = "Equipment Type"
        verbose_name_plural = "Equipment Types"

    def __str__(self):
        return self.name


class Equipment(models.Model):
    """Equipment"""

    name = models.CharField("Name", max_length=200)
    serial_number = models.CharField("Serial Number", max_length=100, blank=True)
    equipment_type = models.ForeignKey(
        EquipmentType,
        on_delete=models.PROTECT,
        verbose_name="Equipment Type",
        related_name="equipment",
    )

    # Parameter values (filled based on schema from equipment_type)
    parameters = JSONField(
        "Parameters",
        schema={},  # Schema will be dynamic based on equipment_type
        default=dict,
        blank=True,
    )

    factories = models.ManyToManyField(
        Equipment_group, verbose_name="Factories", related_name="equipment", blank=True
    )

    installation_date = models.DateField("Installation Date", null=True, blank=True)
    notes = models.TextField("Notes", blank=True)

    class Meta:
        verbose_name = "Equipment"
        verbose_name_plural = "Equipment"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.equipment_type.name})"

    def get_parameter(self, param_name):
        """Get parameter value by name"""
        return self.parameters.get(param_name)

    def set_parameter(self, param_name, value):
        """Set parameter value"""
        self.parameters[param_name] = value
