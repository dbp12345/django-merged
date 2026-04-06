from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import Interaction
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(Interaction)
class InteractionAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("employee__email", "type_of_interaction", "date", "notes")
    autocomplete_fields = ("employee",)
    list_display_links = ("updated_at",)

    list_display = (
        "updated_at",
        "employee",
        "type_of_interaction",
        "date",
        "negative_interaction",
        "notes",
    )
    list_editable = (
        "type_of_interaction",
        "negative_interaction",
    )
    ordering = ("-updated_at",)

    fields = (
        "employee",
        "type_of_interaction",
        "date",
        "notes",
        "negative_interaction",
        (
            "updated_at",
            "modified_by",
        ),
    )
    readonly_fields = (
        "updated_at",
        "modified_by",
    )

    list_filter = ("type_of_interaction", "date", "negative_interaction")
