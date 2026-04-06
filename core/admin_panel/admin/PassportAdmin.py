from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import Passport
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(Passport)
class PassportAdmin(PDFGenerateMixin, FlexListAdmin):
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
        "number",
        "issue_date",
        "expiration_date",
        "document_preview",
        # "modified_by",
    )
    list_editable = ()
    ordering = ("-updated_at",)

    fields = (
        "employee",
        "number",
        "issue_date",
        "expiration_date",
        "document_preview",
        "updated_at",
        "modified_by",
    )
    readonly_fields = (
        "employee",
        "number",
        "issue_date",
        "expiration_date",
        "document_preview",
        "updated_at",
        "modified_by",
    )

    list_filter = ()
