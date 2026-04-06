from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import NomexCheckOut
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(NomexCheckOut)
class NomexCheckOutAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("employee__email", "date", "pants_serial_number", "shirt_serial_number")
    autocomplete_fields = ("employee",)
    list_display_links = ("updated_at",)

    list_display = (
        "updated_at",
        "employee",
        "date",
        "pants_serial_number",
        "shirt_serial_number",
    )
    list_editable = (
        "pants_serial_number",
        "shirt_serial_number",
    )
    ordering = ("-updated_at",)

    fields = (
        "employee",
        "date",
        "pants_serial_number",
        "shirt_serial_number",
        (
            "updated_at",
            "modified_by",
        ),
    )
    readonly_fields = (
        "updated_at",
        "modified_by",
    )

    list_filter = ("date",)
