from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django_admin_flexlist import FlexListAdmin
from core.models.HelpTicket import HelpTicket
from core.models.Task import Category
from dispatch.models.Dispatch import Saw
from pdf_plugin.admin_mixin import PDFGenerateMixin


class HelpTicketInline(admin.TabularInline):
    model = HelpTicket
    fk_name = "saw"

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


@admin.register(Saw)
class SawAdmin(PDFGenerateMixin, FlexListAdmin):
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
            saw=obj,
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
    search_fields = ("model", "serial_number", "make",)
    autocomplete_fields = ("equipment_group",)
    list_display = (
        "__str__",
        "category_for_helptickets",
        "model",
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
        "model",
        "serial_number",
        "condition",
        "make",
        "equipment_group",
        "status",
        # "needs_maintenance",
        # "notes",
    )
    ordering = ("-updated_at",)

    fields = (
        "equipment_group",
        "model",
        "serial_number",
        "condition",
        "make",
        "status",
        # "needs_maintenance",
        "notes",
        "updated_at",
    )
    readonly_fields = (
        "updated_at",
    )

    list_filter = (
        ("equipment_group", RelatedOnlyFieldListFilter),
        "model",
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
