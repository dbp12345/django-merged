from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django_admin_flexlist import FlexListAdmin
from dispatch.models.Dispatch import Truck
from dispatch.models.VehicleCheckout import VehicleCheckout
from core.models.HelpTicket import HelpTicket
from core.models.Task import Category
from pdf_plugin.admin_mixin import PDFGenerateMixin


class VehicleCheckoutInline(admin.TabularInline):
    model = VehicleCheckout
    extra = 0
    readonly_fields = (
        # "__str__",
        "employee",
        "status",
        "milage",
        "license_plate",
        "picture_front_preview",
        "picture_rear_preview",
        "picture_driver_side_preview",
        "picture_passenger_side_preview",
        "updated_at",
        "created_at",
    )
    fields = (
        # "__str__",
        "employee",
        "status",
        "milage",
        "license_plate",
        "picture_front_preview",
        "picture_rear_preview",
        "picture_driver_side_preview",
        "picture_passenger_side_preview",
        "updated_at",
    )
    can_delete = False
    show_change_link = True


class HelpTicketInline(admin.TabularInline):
    model = HelpTicket
    fk_name = "truck"

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


@admin.register(Truck)
class TruckAdmin(PDFGenerateMixin, FlexListAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("equipment_group")

    class Media:
        css = {
            "all": (
                "admin/css/light.css",
            )
        }

    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    inlines = [HelpTicketInline, VehicleCheckoutInline]

    list_per_page = 100
    search_fields = (
        "key",
        "make",
        "model",
        "license_plate",
        "year",
        "vin_number",
        "serial_number",
        "color",
        "fuel_type",
        "registration_state",
    )
    autocomplete_fields = ("equipment_group",)

    # list_display_links = ("updated_at",)

    @admin.display(description="Contracts")
    def contracts_display(self, obj):
        # return ", ".join([c.number for c in obj.contracts_entries.all()])
        return format_html(
            "<ul style='font-style: italic;'>"
            "{}"
            "</ul>",
            format_html_join(
                "",
                "<li><a href='{}'>{}</a></li>",
                (
                    (
                        reverse("admin:dispatch_contracts_change", args=[c.pk]),
                        str(c),
                    )
                    for c in obj.contracts_entries.all()
                )
            )
        )

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
            truck=obj,
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

    list_display = (
        "__str__",
        "category_for_helptickets",
        "key",
        "model",
        "license_plate",
        # "serial_number",
        "owner",
        "year",
        "milage",
        # "passengers",
        "vin_number",
        "equipment_group",
        # "gvwr",
        "color",
        "fuel_type",
        # "insurance_expiration_date",
        # "registration_expiration_date",
        # "next_service_date",
        # "insurance_provider",
        "registration_state",

        # "picture_front_preview",
        # "picture_rear_preview",
        # "picture_driver_side_preview",
        # "picture_passenger_side_preview",
        "make",
        "status",
        "number_of_doors",
        "drive",
        "motor",
        "dot_inspection_date",
        "dot_inspection_file",
        # "needs_maintenance",
        "contracts_display",
        "notes",
        # "qr_code_preview",
        # "updated_at",
    )
    list_editable = (
        "model",
        "key",
        "license_plate",
        # "serial_number",
        "owner",
        "year",
        "milage",
        # "passengers",
        "vin_number",
        "equipment_group",
        # "gvwr",
        "color",
        "fuel_type",
        # "insurance_expiration_date",
        # "registration_expiration_date",
        # "next_service_date",
        # "insurance_provider",
        "registration_state",
        "make",
        "status",
        "number_of_doors",
        "drive",
        "motor",
        "dot_inspection_date",
        "dot_inspection_file",
        # "needs_maintenance",
        # "notes",
    )
    ordering = ("-updated_at",)

    fields = (
        "key",
        "equipment_group",
        "model",
        "license_plate",
        "serial_number",
        "owner",
        "year",
        "milage",
        "passengers",
        "vin_number",
        "gvwr",
        "color",
        "fuel_type",
        "insurance_expiration_date",
        "registration_expiration_date",
        "next_service_date",
        "insurance_provider",
        "registration_state",
        "make",
        ("picture_front", "picture_front_preview"),
        ("picture_rear", "picture_rear_preview"),
        ("picture_driver_side", "picture_driver_side_preview"),
        ("picture_passenger_side", "picture_passenger_side_preview"),
        ("qr_code", "qr_code_preview"),
        "status",
        "number_of_doors",
        "drive",
        "motor",
        "dot_inspection_date",
        "dot_inspection_file",
        # "needs_maintenance",
        "contracts_display",
        "notes",
        "updated_at",
    )
    readonly_fields = (
        "picture_front_preview",
        "picture_rear_preview",
        "picture_driver_side_preview",
        "picture_passenger_side_preview",
        "qr_code_preview",
        "contracts_display",
        "updated_at",
    )

    list_filter = (
        "owner",
        ("equipment_group", RelatedOnlyFieldListFilter),
        "model",
        "year",
        "color",
        "fuel_type",
        "registration_state",
        "make",
        "status",
        "drive",
        # "needs_maintenance",
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        for name in ("equipment_group",):
            f = form.base_fields.get(name)
            if not f:
                continue
            w = f.widget
            if isinstance(w, RelatedFieldWidgetWrapper):
                w.can_delete_related = False  # убираем опасный крестик удаления

        return form
