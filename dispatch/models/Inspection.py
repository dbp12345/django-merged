from django.db import models
from eav.decorators import register_eav
from eav.registry import EavConfig
from eav.models import Attribute
from core.utils import model_directory_path
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from privser.models.Contacts import Contacts


class InspectionType(models.Model):
    """Inspection type with configuration for EAV attributes"""

    name = models.CharField("Type name", max_length=255)
    description = models.TextField("Description", blank=True, null=True)

    # Configuration: which EAV attributes to use for this type
    eav_attributes_config = models.JSONField(
        "EAV Attributes configuration",
        default=list,
        blank=True,
        help_text=(
            "List of EAV attribute slugs to display for this inspection type. "
            'Example: ["mileage", "condition", "notes"]'  # noqa: E501
        ),
    )

    class Meta:
        verbose_name = "Inspection Type"
        verbose_name_plural = "Inspection Types"
        ordering = ["name"]

    def __str__(self):
        return self.name


class InspectionEavConfig(EavConfig):
    """
    Custom EAV Config for Inspection that filters attributes
    based on inspection_type.eav_attributes_config
    """

    @classmethod
    def get_attributes(cls, instance=None):
        """
        Filter attributes based on inspection_type configuration
        """
        if instance:
            # Check if inspection_type_id exists first (avoid RelatedObjectDoesNotExist)
            inspection_type_id = getattr(instance, 'inspection_type_id', None)
            if inspection_type_id:
                try:
                    inspection_type = instance.inspection_type
                    if inspection_type and inspection_type.eav_attributes_config:
                        attribute_slugs = inspection_type.eav_attributes_config
                        if attribute_slugs:
                            return Attribute.objects.filter(slug__in=attribute_slugs)
                except Exception:
                    # inspection_type not accessible yet
                    pass
        # If no type selected or no config, return empty queryset
        return Attribute.objects.none()


@register_eav(config_cls=InspectionEavConfig)
class Inspection(models.Model):
    """Inspection model with EAV support for dynamic parameters"""

    # Basic required fields
    inspection_type = models.ForeignKey(
        InspectionType,
        on_delete=models.PROTECT,
        verbose_name="Inspection type",
        related_name="inspections",
    )

    # Required fields from PM requirements
    inspector = models.ForeignKey(
        Contacts,
        on_delete=models.SET_NULL,
        verbose_name="Inspector",
        related_name="inspections",
        blank=True,
        null=True,
        help_text="Inspector can be a relation to a contact",
    )
    file = models.ImageField(
        "File",
        upload_to=model_directory_path,
        blank=True,
        null=True,
        help_text="Inspection file/document",
    )
    date = models.DateField(
        "Date",
        blank=True,
        null=True,
        help_text="Inspection date",
    )

    # Additional metadata
    notes = models.TextField("Notes", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "Inspection"
        verbose_name_plural = "Inspections"
        ordering = ["-date", "-updated_at"]

    def __str__(self):
        type_name = self.inspection_type.name if self.inspection_type else "Unknown"
        date_str = self.date.strftime("%Y-%m-%d") if self.date else "No date"
        return f"{type_name} - {date_str}"

    def get_all_eav_values(self):
        """Get all EAV attribute values for this inspection"""
        from eav.models import Value
        ct = ContentType.objects.get_for_model(self)
        return Value.objects.filter(entity_ct=ct, entity_id=self.pk)


class InspectionRelatedItem(models.Model):
    """Related items for Inspection - can link to Equipment, Truck, Saw, Phone, Radio"""

    inspection = models.ForeignKey(
        Inspection,
        on_delete=models.CASCADE,
        verbose_name="Inspection",
        related_name="related_items",
    )

    # GenericForeignKey fields
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Related object type",
    )
    object_id = models.PositiveIntegerField(verbose_name="Related object ID")
    content_object = GenericForeignKey("content_type", "object_id")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Related Item"
        verbose_name_plural = "Related Items"
        ordering = ["-updated_at"]

    def __str__(self):
        obj_type = self.content_type.model_class().__name__ if self.content_type else "Unknown"
        obj_str = str(self.content_object) if self.content_object else f"ID: {self.object_id}"
        return f"{obj_type}: {obj_str}"
