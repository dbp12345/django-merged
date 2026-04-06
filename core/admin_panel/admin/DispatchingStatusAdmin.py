from django.contrib import admin
from django.utils.safestring import mark_safe
from django_admin_flexlist import FlexListAdmin

from company.models.Employees import DispatchingStatus, DispatchStatus
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(DispatchingStatus)
class DispatchingStatusAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("employee__email", "dispatch_status",)
    autocomplete_fields = ("employee",)
    list_display_links = ("updated_at",)

    list_display = (
        #                "Dispatch Call Status",
        #         "Dispatch Category",
        #         "ETA, Late, Dispatch",
        #         "Dispatch location",
        #         "Dispatch notes",
        "updated_at",
        "employee",
        "dispatch_status",
        "status_preview",
        "dispatch_category",
        "ETA",
        "location",
        "positive_interaction",
        "notes",
        # "date",
        # "modified_by",
    )
    ordering = ("-updated_at",)

    list_editable = (
        "dispatch_status",
        "positive_interaction",
        "ETA",
        "location",
    )

    fields = (
        "employee",
        "dispatch_status",
        "dispatch_category",
        "ETA",
        "location",
        "positive_interaction",
        "notes",
        # "date",
        ("updated_at", "modified_by",)
    )
    readonly_fields = (
        # "employee",
        "updated_at",
        "modified_by",
    )

    list_filter = ("dispatch_status",)

    @admin.display(description="Color")
    def status_preview(self, obj):
        color = DispatchStatus.get_color_by_name(obj.dispatch_status)
        return mark_safe(
            f'<div style="width: 100px; height: 20px; background-color: {color}; border: 1px solid #000;"></div>'
        )
