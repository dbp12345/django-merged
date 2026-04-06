from django.contrib import admin
from django_admin_flexlist import FlexListAdmin

from company.models.Employees import DriverLicense
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(DriverLicense)
class DriverLicenseAdmin(PDFGenerateMixin, FlexListAdmin):
    def has_add_permission(self, request):
        return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("employee__email",)
    autocomplete_fields = ("employee",)
    list_display_links = ("updated_at",)

    list_display = (
        "updated_at",
        "employee",
        "issue_date",
        "expiration_date",
        "number",
        "endorsement",
        "restriction",
        "front_of_id_preview",
        "back_of_id_preview",
        "id_2_front_preview",
        "id_2_back_preview",
        # "modified_by",
    )
    list_editable = ()
    ordering = ("-updated_at",)

    fields = (
        "employee",
        "issue_date",
        "expiration_date",
        "number",
        "endorsement",
        "restriction",
        "front_of_id_preview",
        "back_of_id_preview",
        "id_2_front_preview",
        "id_2_back_preview",
        "updated_at",
        "modified_by",
    )
    readonly_fields = (
        "employee",
        "issue_date",
        "expiration_date",
        "number",
        "endorsement",
        "restriction",
        "front_of_id_preview",
        "back_of_id_preview",
        "id_2_front_preview",
        "id_2_back_preview",
        "updated_at",
        "modified_by",
    )

    list_filter = ()
