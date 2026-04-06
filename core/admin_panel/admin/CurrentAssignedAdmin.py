from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import CurrentAssigned
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(CurrentAssigned)
class CurrentAssignedAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("employee__email", "date")
    autocomplete_fields = ("employee",)
    list_display_links = ("updated_at",)

    list_display = (
        "updated_at",
        "employee",
        "date",
        # "modified_by",
    )
    list_editable = (
        "date",
    )
    ordering = ("-updated_at",)

    fields = (
        "employee",
        "date",
        ("updated_at", "modified_by",)
    )
    readonly_fields = (
        # "employee",
        "updated_at",
        "modified_by",
    )

    list_filter = ("date",)
