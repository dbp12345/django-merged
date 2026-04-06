from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import TaskBook
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(TaskBook)
class TaskBookAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("employee__email", "type_of_taskbook", "initiated_date", "completed_date")
    autocomplete_fields = ("employee",)
    list_display_links = ("updated_at",)

    list_display = (
        "updated_at",
        "employee",
        "type_of_taskbook",
        "initiated_date",
        "completed_date",
        "updated_date",
        "final_evaluator",
        "document",
        "document_preview",
    )
    list_editable = (
        "type_of_taskbook",
        "initiated_date",
        "completed_date",
        "updated_date",
        "final_evaluator",
        "document",
    )
    ordering = ("-updated_at", )

    fields = (
        "employee",
        "type_of_taskbook",
        "initiated_date",
        "completed_date",
        "updated_date",
        "final_evaluator",
        "document",
        "document_preview",
        ("updated_at", "modified_by",)
    )
    readonly_fields = (
        "updated_at",
        "modified_by",
        "document_preview",
    )

    list_filter = ("type_of_taskbook",)
