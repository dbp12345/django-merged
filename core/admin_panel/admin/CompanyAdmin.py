from django.contrib import admin
from django_admin_flexlist import FlexListAdmin

from company.models import Company
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(Company)
class CompanyAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    def has_delete_permission(self, request, obj=None):
        return False

    list_per_page = 100
    search_fields = ("name", "address")
    list_display = (
        # "updated_at",
        "name",
        "address",
        "phone",
        "dot",
        "tax",
        "mspa",
        "email",
        "articles_of_organization_file",
        "mspa_license_file",
        "updated_at",
    )
    list_editable = (
        # "name",
        "address",
        "phone",
        "dot",
        "tax",
        "mspa",
        "email",
        "articles_of_organization_file",
        "mspa_license_file",
    )
    ordering = ()

    fields = (
        "name",
        "address",
        "phone",
        "dot",
        "tax",
        "mspa",
        "email",
        "articles_of_organization_file",
        "mspa_license_file",
        "updated_at",
    )
    readonly_fields = (
        "updated_at",
    )

    list_filter = ("updated_at",)

