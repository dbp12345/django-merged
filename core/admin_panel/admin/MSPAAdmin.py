from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import MSPA
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(MSPA)
class MSPAAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    # def file_link(self, obj):
    #     if obj.link_to_document:
    #         url = obj.link_to_document.url
    #         file_name = os.path.basename(obj.link_to_document.name)
    #         return format_html('<a href="{}">{}</a>', url, file_name)
    #     return '-'
    # file_link.short_description = 'document'

    list_per_page = 100
    search_fields = ("employee__email", "MSPA_number",)
    autocomplete_fields = ("employee",)
    list_display_links = ("updated_at",)

    list_display = (
        "updated_at",
        "employee",
        "issue_date",
        "expiration_date",
        "MSPA_number",
        "pending",
        # "file_link",
        "document",
        "document_preview",
    )
    list_editable = (
        "document",
        # "dispatch_status",
    )
    ordering = ("-updated_at",)

    fields = (
        "employee",
        "issue_date",
        "expiration_date",
        "MSPA_number",
        "pending",
        "document",
        "document_preview",
    )
    readonly_fields = (
        "updated_at",
        "modified_by",
        "document_preview",
    )

    list_filter = ()
