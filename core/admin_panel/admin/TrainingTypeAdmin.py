from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import TrainingType
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(TrainingType)
class TrainingTypeAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("name", )
    list_display = (
        # "updated_at",
        "name",
        "updated_at",
        # "modified_by",
    )
    list_editable = (
        # "name",
    )
    fields = (
        "name",
        (
            "updated_at",
            "modified_by",
        ),
    )
    readonly_fields = (
        "updated_at",
        "modified_by",
    )
    ordering = ("name",)
