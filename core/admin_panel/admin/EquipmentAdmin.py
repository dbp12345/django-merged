from dal import autocomplete
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.forms import ModelForm, ModelMultipleChoiceField, MultipleChoiceField
from django.forms.widgets import CheckboxSelectMultiple
from django_admin_flexlist import FlexListAdmin
from core.models.HelpTicket import HelpTicket
from core.models.Task import Category
from dispatch.models.Equipment import (
    EquipmentType,
    Equipment,
    PARAMETER_FIELDS,
)
from dispatch.models.Dispatch import Equipment_group
from pdf_plugin.admin_mixin import PDFGenerateMixin


class HelpTicketInline(admin.TabularInline):
    model = HelpTicket
    fk_name = "equipment"

    fields = (
        "title",
        "created_for",
        "assigned_to",
        "status",
        "priority",
        # "document_preview",
        "category",
        # "tools",
        # "created_by",
        # "created_by_admin",
        "updated_at",
    )
    readonly_fields = (
        "title",
        "created_for",
        "assigned_to",
        "status",
        "priority",
        # "document_preview",
        "category",
        # "tools",
        # "created_by",
        # "created_by_admin",
        "updated_at",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(status="completed")

    def has_add_permission(self, request, obj=None):
        return False

    extra = 0
    show_change_link = True
    can_delete = False
    ordering = (
        "-priority",
        "-updated_at",
    )


class EquipmentTypeForm(ModelForm):
    """Form with checkboxes for selecting parameters"""

    available_parameters = MultipleChoiceField(
        required=False,
        widget=CheckboxSelectMultiple,
        label="Available Parameters",
        help_text="Select parameters to enable for this equipment type",
        choices=[(key, label) for key, label in PARAMETER_FIELDS.items()],
    )

    class Meta:
        model = EquipmentType
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial value from fields_config
        if self.instance and self.instance.pk and self.instance.fields_config:
            self.fields["available_parameters"].initial = self.instance.fields_config

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Save selected parameters to fields_config
        instance.fields_config = self.cleaned_data.get("available_parameters", [])
        if commit:
            instance.save()
        return instance


@admin.register(EquipmentType)
class EquipmentTypeAdmin(PDFGenerateMixin, FlexListAdmin):
    form = EquipmentTypeForm
    list_display = ["name", "equipment_count"]
    search_fields = ["name", "description"]

    fieldsets = (
        ("General Information", {"fields": ("name", "description")}),
        (
            "Parameter Configuration",
            {
                "fields": ("available_parameters",),
                "description": "Select parameters that should be available for this equipment type",
            },
        ),
        # (
        #     "Fields Config (Auto-generated)",
        #     {
        #         "fields": ("fields_config",),
        #         "classes": ("collapse",),
        #         "description": "Auto-generated based on selected parameters above",
        #     },
        # ),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Make fields_config readonly
        # form.base_fields["fields_config"].widget.attrs["readonly"] = True
        return form

    def equipment_count(self, obj):
        return obj.equipment.count()

    equipment_count.short_description = "Equipment count"


class DynamicEquipmentForm(ModelForm):
    """Form that shows only configured fields based on equipment_type"""

    equipment_group = ModelMultipleChoiceField(
        queryset=Equipment_group.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="equipment-group-autocomplete", forward=["instance_id"]
        ),
    )

    class Meta:
        model = Equipment
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = self.instance

        # Setup equipment_group field with autocomplete
        if instance.pk and "instance_id" not in self.data:
            self.data = self.data.copy()
            self.data["instance_id"] = str(instance.pk)

        if instance.pk:
            # Get currently selected equipment groups
            selected = list(instance.equipment_group.all())
            self.fields["equipment_group"].queryset = Equipment_group.objects.all()
            self.fields["equipment_group"].initial = selected
        else:
            self.fields["equipment_group"].queryset = Equipment_group.objects.all()

        # Get all parameter field names from PARAMETER_FIELDS
        all_parameter_fields = set(PARAMETER_FIELDS.keys())

        # Get equipment_type and configured fields
        equipment_type = None
        configured_fields = []

        if self.instance and self.instance.pk:
            # Existing equipment - use its equipment_type
            equipment_type = self.instance.equipment_type
        elif "equipment_type" in self.data:
            # New equipment - try to get equipment_type from form data
            try:
                equipment_type_id = self.data.get("equipment_type")
                if equipment_type_id:
                    equipment_type = EquipmentType.objects.get(pk=equipment_type_id)
            except (EquipmentType.DoesNotExist, ValueError, TypeError):
                pass

        # Get configured fields if equipment_type exists
        if equipment_type and equipment_type.fields_config:
            configured_fields = equipment_type.fields_config

        # Hide all parameter fields by default
        # Show only if they are in configured_fields
        for field_name in self.fields:
            if field_name in all_parameter_fields:
                if field_name not in configured_fields:
                    # Hide parameter field if not configured
                    self.fields[field_name].widget = self.fields[
                        field_name
                    ].hidden_widget()
                    self.fields[field_name].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()

        # Handle ManyToMany equipment_group
        if instance.pk:
            selected_groups = self.cleaned_data.get("equipment_group", [])
            instance.equipment_group.set(selected_groups)

        return instance


@admin.register(Equipment)
class EquipmentAdmin(PDFGenerateMixin, FlexListAdmin):
    form = DynamicEquipmentForm

    search_fields = ["name", "serial_number", "notes"]
    list_filter = ["equipment_type", ("equipment_group", RelatedOnlyFieldListFilter)]
    date_hierarchy = "updated_at"

    @admin.display(description="Needs maintenance")
    def category_for_helptickets(self, obj):
        # Find Equipment category
        try:
            equipment_category = Category.objects.get(name="Equipment")
        except Category.DoesNotExist:
            return ""
        
        # Get all children categories of Equipment
        equipment_children = equipment_category.get_children()
        equipment_children_ids = list(equipment_children.values_list("id", flat=True))
        
        help_tickets = HelpTicket.objects.filter(
            equipment=obj,
            category_id__in=equipment_children_ids
        ).exclude(status="completed").select_related("category")
        
        # Get unique categories
        categories = set()
        for ticket in help_tickets:
            if ticket.category:
                categories.add(ticket.category)
        
        if not categories:
            return ""
        
        # Display categories as links
        return format_html(
            "<ul style='font-style: italic;'>"
            "{}"
            "</ul>",
            format_html_join(
                "",
                "<li><a href='{}'>{}</a></li>",
                (
                    (
                        reverse("admin:core_category_change", args=[cat.pk]),
                        str(cat),
                    )
                    for cat in sorted(categories, key=lambda x: x.name)
                )
            )
        )

    inlines = [HelpTicketInline]

    def get_fieldsets(self, request, obj=None):
        """Dynamic fieldsets: minimal fields for new equipment, full for existing"""
        if obj is None:
            # Creating new equipment - show only basic fields
            return (
                (
                    None,
                    {
                        "fields": (
                            "equipment_type",
                            "name",
                            "serial_number",
                        )
                    },
                ),
            )
        else:
            # Editing existing equipment - show configured parameters
            fieldsets = [
                (
                    None,
                    {
                        "fields": (
                            "equipment_type",
                            "name",
                            "serial_number",
                        )
                    },
                ),
            ]

            # Add configured parameters if equipment_type has fields_config
            if obj.equipment_type and obj.equipment_type.fields_config:
                configured_fields = [
                    field
                    for field in obj.equipment_type.fields_config
                    if field in PARAMETER_FIELDS
                ]
                if configured_fields:
                    fieldsets.append(
                        (
                            "Parameters",
                            {
                                "fields": tuple(configured_fields),
                            },
                        )
                    )

            # Add equipment_group and notes
            fieldsets.extend(
                [
                    ("Equipment Group", {"fields": ("equipment_group",)}),
                    ("Notes", {"fields": ("notes",)}),
                ]
            )

            return tuple(fieldsets)

    @admin.display(description="Equipment Groups")
    def equipment_groups_display(self, obj):
        """Display list of equipment groups with links"""
        groups = obj.equipment_group.all()
        if not groups.exists():
            return "-"

        def link_for(group):
            url = reverse(
                f"admin:{group._meta.app_label}_{group._meta.model_name}_change",
                args=[group.pk],
            )
            return format_html(
                '<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>',
                url,
                str(group),
            )

        return format_html(
            "<ul style='margin: 0; padding-left: 1.2em; list-style-type: disc;'>{}</ul>",
            format_html_join("", "<li>{}</li>", ((link_for(g),) for g in groups)),
        )

    def get_list_display(self, request):
        """Show all parameters in list display - user configures via FlexListAdmin"""
        # base_fields = ["name", "equipment_group", "equipment_type"]
        base_fields = ["name", "equipment_type", "category_for_helptickets", "equipment_groups_display"]
        return base_fields + list(PARAMETER_FIELDS.keys())

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related("equipment_type").prefetch_related("equipment_group")
