from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.forms import ModelForm, MultipleChoiceField
from django.forms.widgets import CheckboxSelectMultiple
from django_admin_flexlist import FlexListAdmin
from eav.admin import BaseEntityAdmin
from eav.forms import BaseDynamicEntityForm
from eav.models import Attribute, Value
from dispatch.models.Inspection import Inspection, InspectionType, InspectionRelatedItem
from pdf_plugin.admin_mixin import PDFGenerateMixin


class InspectionTypeForm(ModelForm):
    """Form with checkboxes for selecting EAV attributes"""

    available_attributes = MultipleChoiceField(
        required=False,
        widget=CheckboxSelectMultiple,
        label="Available EAV Attributes",
        help_text="Select EAV attributes to enable for this inspection type",
    )

    class Meta:
        model = InspectionType
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get all available EAV attributes and create choices
        attributes = Attribute.objects.all().order_by("name")
        self.fields["available_attributes"].choices = [
            (attr.slug, f"{attr.name} ({attr.slug})") for attr in attributes
        ]

        # Set initial value from eav_attributes_config
        if self.instance and self.instance.pk and self.instance.eav_attributes_config:
            self.fields["available_attributes"].initial = self.instance.eav_attributes_config

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Save selected attributes to eav_attributes_config
        instance.eav_attributes_config = self.cleaned_data.get("available_attributes", [])
        if commit:
            instance.save()
        return instance


@admin.register(InspectionType)
class InspectionTypeAdmin(PDFGenerateMixin, FlexListAdmin):
    """Admin for InspectionType"""

    form = InspectionTypeForm
    list_display = ["name", "description", "inspection_count"]
    search_fields = ["name", "description"]

    fieldsets = (
        ("General Information", {"fields": ("name", "description")}),
        (
            "EAV Attributes Configuration",
            {
                "fields": ("available_attributes",),
                "description": "Select EAV attributes that should be available for this inspection type",
            },
        ),
    )

    def inspection_count(self, obj):
        """Count inspections of this type"""
        return obj.inspections.count()

    inspection_count.short_description = "Inspections count"


class InspectionForm(BaseDynamicEntityForm):
    """Form for Inspection with EAV support that respects inspection_type"""

    class Meta:
        model = Inspection
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        # Handle inspection_type from form data for new objects
        if "data" in kwargs and kwargs["data"]:
            data = kwargs["data"].copy()
            inspection_type_id = data.get("inspection_type")
            if inspection_type_id and not (kwargs.get("instance") and kwargs["instance"].pk):
                # For new inspections, set inspection_type before super().__init__
                try:
                    inspection_type = InspectionType.objects.get(pk=inspection_type_id)
                    if not kwargs.get("instance"):
                        kwargs["instance"] = Inspection()
                    kwargs["instance"].inspection_type = inspection_type
                except (InspectionType.DoesNotExist, ValueError, TypeError):
                    pass

        super().__init__(*args, **kwargs)


class InspectionRelatedItemInline(admin.TabularInline):
    """Inline for managing related items (Equipment, Truck, Saw, Phone, Radio)"""
    model = InspectionRelatedItem
    extra = 1
    autocomplete_fields = []  # GenericForeignKey doesn't support autocomplete directly
    fields = ("content_type", "object_id")
    verbose_name = "Related Item"
    verbose_name_plural = "Related Items"

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Limit content_type choices to allowed models
        from dispatch.models.Dispatch import Truck, Saw, Phone, Radio
        from dispatch.models.Equipment import Equipment
        
        allowed_models = [Equipment, Truck, Saw, Phone, Radio]
        ct_ids = [ContentType.objects.get_for_model(m).id for m in allowed_models]
        
        formset.form.base_fields["content_type"].queryset = ContentType.objects.filter(id__in=ct_ids)
        return formset


@admin.register(Inspection)
class InspectionAdmin(PDFGenerateMixin, BaseEntityAdmin, FlexListAdmin):
    """Admin for Inspection with EAV support"""

    form = InspectionForm
    inlines = [InspectionRelatedItemInline]

    list_filter = ["inspection_type", "date"]
    search_fields = ["notes", "inspector__email"]
    date_hierarchy = "date"

    autocomplete_fields = ["inspector"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "inspection_type",
                    "date",
                    "inspector",
                    "file",
                )
            },
        ),
        ("Notes", {"fields": ("notes",)}),
        (
            "Metadata",
            {
                "fields": ("updated_at", "modified_by"),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ["updated_at", "modified_by"]

    def related_items_display(self, obj):
        """Display related items in list view"""
        if not obj.pk:
            return "-"
        items = obj.related_items.select_related("content_type").all()
        if not items.exists():
            return "-"
        items_list = []
        for item in items:
            if item.content_object:
                items_list.append(str(item.content_object))
        return ", ".join(items_list) if items_list else "-"
    
    related_items_display.short_description = "Related Items"
    
    def _get_all_eav_attributes(self):
        """Get all EAV attributes used in any InspectionType"""
        all_slugs = set()
        for inspection_type in InspectionType.objects.all():
            if inspection_type.eav_attributes_config:
                all_slugs.update(inspection_type.eav_attributes_config)
        return Attribute.objects.filter(slug__in=all_slugs).order_by("name")

    def _create_eav_attribute_display_method(self, attribute):
        """Create a simple method to display EAV attribute value"""
        attr_slug = attribute.slug
        attr_name = attribute.name

        def display_method(self, obj):
            """Display EAV attribute value"""
            if not obj.pk:
                return "-"
            try:
                ct = ContentType.objects.get_for_model(Inspection)
                value = Value.objects.filter(
                    entity_ct=ct,
                    entity_id=obj.pk,
                    attribute=attribute
                ).first()
                if value:
                    return str(value.value) if value.value is not None else "-"
            except Exception:
                pass
            return "-"

        method_name = f"eav_attr_{attr_slug}"
        display_method.short_description = attr_name
        return method_name, display_method

    def get_dynamic_eav_fields(self):
        """Get list of dynamic EAV attribute field names for list display"""
        fields = []
        attributes = self._get_all_eav_attributes()

        for attribute in attributes:
            method_name, method_func = self._create_eav_attribute_display_method(attribute)

            # Create method on class if not exists
            if not hasattr(self.__class__, method_name):
                setattr(self.__class__, method_name, method_func)

            fields.append(method_name)

        return fields

    def get_fieldsets(self, request, obj=None):
        """Add EAV attributes fieldset if object exists"""
        fieldsets = list(super().get_fieldsets(request, obj))
        return tuple(fieldsets)

    def get_list_display(self, request):
        """Show base fields + dynamic EAV attribute fields"""
        base_fields = [
            "inspection_type",
            "date",
            "inspector",
            "related_items_display",
            "updated_at",
        ]
        eav_fields = self.get_dynamic_eav_fields()
        return base_fields + eav_fields

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            "inspection_type",
            "inspector",
        ).prefetch_related("related_items", "related_items__content_type")

    def save_model(self, request, obj, form, change):
        """Set modified_by on save"""
        if not change:
            obj.modified_by = request.user.username if request.user.is_authenticated else "system"
        super().save_model(request, obj, form, change)
