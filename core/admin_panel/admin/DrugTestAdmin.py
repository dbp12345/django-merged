from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import DrugTest
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(DrugTest)
class DrugTestAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("employee__email", "date",)
    autocomplete_fields = ("employee",)
    list_display_links = ("updated_at",)

    list_display = (
        "updated_at",
        "employee",
        "date",
        "result",
        # "modified_by",
    )
    list_editable = (
        "date",
        "result",
    )
    ordering = ("-updated_at",)

    fields = (
        "employee",
        "date",
        "result",
        ("modified_by",
         "updated_at",)
    )
    readonly_fields = (
        # "employee",
        "updated_at",
        "modified_by",
    )

    list_filter = ("date",)
