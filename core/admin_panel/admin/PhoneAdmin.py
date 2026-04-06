from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django_admin_flexlist import FlexListAdmin
from core.models.HelpTicket import HelpTicket
from core.models.Task import Category
from core.models import Mqtt_Log
from core.services.MqttScansService import MqttScansService
from dispatch.models.Dispatch import Phone
from pdf_plugin.admin_mixin import PDFGenerateMixin


class HelpTicketInline(admin.TabularInline):
    model = HelpTicket
    fk_name = "phone"

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


def beacon_visits_block_for_admin(self, obj, request):
    if not obj.name:
        return ""

    data = list(Mqtt_Log.objects.filter(
        topic="crew/boss",
        beacon__isnull=False,
        phone=obj.name
    ).order_by("timestamp").values_list("timestamp", "beacon"))
    row = [{"timestamp": ts, "beacon_id": beacon} for ts, beacon in data]
    res = MqttScansService.detect_visits(beacon_logs=row)

    html = render_to_string("admin/scans/index.html", {
        "res": res
    }, request=request)

    return mark_safe(html)


@admin.register(Phone)
class PhoneAdmin(PDFGenerateMixin, FlexListAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("equipment_group")
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    # list_display_links = ("updated_at",)

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
            phone=obj,
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

    list_per_page = 100
    search_fields = ("name", "model", "number", "os", "pin", "imei", "serial_number", "make",)
    autocomplete_fields = ("equipment_group",)
    list_display = (
        "__str__",
        "category_for_helptickets",
        "name",
        "model",
        "number",
        "os",
        "pin",
        "imei",
        "serial_number",
        "condition",
        "make",
        "equipment_group",
        "status",
        # "needs_maintenance",
        "notes",
        # "updated_at",
    )
    list_editable = (
        "name",
        "model",
        "number",
        "os",
        "pin",
        "imei",
        "serial_number",
        "condition",
        "make",
        "equipment_group",
        "status",
        # "needs_maintenance",
        # "notes",
    )
    ordering = ("-updated_at",)

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (None, {
                "fields": (
                    "equipment_group",
                    "name",
                    "model",
                    "number",
                    "os",
                    "pin",
                    "imei",
                    "serial_number",
                    "condition",
                    "make",
                    "status",
                    # "needs_maintenance",
                    "notes",
                    "updated_at",
                ),
            }),
        ]

        if obj:
            fieldsets.append(
                (
                    None,
                    {
                        "fields": (),
                        "description": beacon_visits_block_for_admin(
                            self, obj, request
                        ),
                    },
                )
            )

        return fieldsets

    readonly_fields = (
        "updated_at",
    )

    list_filter = (
        ("equipment_group", RelatedOnlyFieldListFilter),
        "model",
        "os",
        "condition",
        "make",
        "status",
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
