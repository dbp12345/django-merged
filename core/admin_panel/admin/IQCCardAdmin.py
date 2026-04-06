from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import IQCCard
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(IQCCard)
class IQCCardAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("employee__email", "position", "pack_test", "date")
    autocomplete_fields = ("employee",)
    list_display_links = ("updated_at",)

    list_display = (
        "updated_at",
        "employee",
        "position",
        "pack_test",
        "document_preview",
        "date",
        # "modified_by",
    )
    list_editable = (
        "position",
        "pack_test",
        "date",
    )
    ordering = ("-updated_at",)

    fields = (
        "employee",
        "position",
        "pack_test",
        "document",
        "document_preview",
        "date",
        "updated_at",
        "modified_by",
    )
    readonly_fields = (
        "document_preview",
        "updated_at",
        "modified_by",
    )

    list_filter = ("date",)
