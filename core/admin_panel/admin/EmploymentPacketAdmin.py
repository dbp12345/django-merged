from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import EmploymentPacket
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(EmploymentPacket)
class EmploymentPacketAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("employee__email", "packet_name", "date_sent", "date_signed")
    autocomplete_fields = ("employee",)
    list_display_links = ("updated_at",)

    list_display = (
        "updated_at",
        "employee",
        "packet_name",
        "date_sent",
        "date_signed",
        "document",
        "document_preview",
        # "modified_by",
    )
    list_editable = (
        "packet_name",
        "date_sent",
        "date_signed",
        "document",
    )
    ordering = ("-updated_at",)

    fields = (
        "employee",
        "packet_name",
        "date_sent",
        "date_signed",
        "document",
        "document_preview",
        (
            "updated_at",
            "modified_by",
        ),
    )
    readonly_fields = (
        # "employee",
        "updated_at",
        "modified_by",
        "document_preview",
    )

    list_filter = ()
