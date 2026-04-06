from django.contrib import admin
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django_admin_flexlist import FlexListAdmin
from dispatch.models.Dispatch import Nomex
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(Nomex)
class NomexAdmin(PDFGenerateMixin, FlexListAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("equipment_group")
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    # list_display_links = ("updated_at",)

    list_per_page = 100
    search_fields = ()
    autocomplete_fields = ("equipment_group",)
    list_display = (
        "updated_at",
        "__str__",
        "type",
        "size",
        "serial_number",
        "condition",
        "equipment_group",
        "status",
        # "needs_maintenance",
        "notes",
    )
    list_editable = (
        "equipment_group",
        "type",
        "size",
        "serial_number",
        "condition",
        "status",
        # "needs_maintenance",
        # "notes",
    )
    ordering = ("-updated_at",)

    fields = (
        "equipment_group",
        "type",
        "size",
        "serial_number",
        "condition",
        "status",
        # "needs_maintenance",
        "notes",
        "updated_at",
    )
    readonly_fields = (
        "updated_at",
    )

    list_filter = ("equipment_group", "status",)

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
