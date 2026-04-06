from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import Evaluation
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(Evaluation)
class EvaluationAdmin(PDFGenerateMixin, FlexListAdmin):
    list_per_page = 100
    search_fields = ("crew__fire__incident_name",)
    autocomplete_fields = ("crew",)
    list_display = (
        "updated_at",
        "crew",
        "rated_by",
        "date",
        "hotline",
        "document",
        "document_preview",
        # "modified_by",
    )
    list_editable = (
        "crew",
        "rated_by",
        "date",
        "hotline",
        "document",
    )
    ordering = ()

    fields = (
        "crew",
        "rated_by",
        "date",
        "hotline",
        "document",
        "document_preview",
        ("updated_at", "modified_by"),
    )
    readonly_fields = (
        "updated_at",
        "modified_by",
        "document_preview",
    )

    list_filter = ("crew",)
