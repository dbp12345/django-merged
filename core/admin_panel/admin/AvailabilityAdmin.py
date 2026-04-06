from django.contrib import admin
from django_admin_flexlist import FlexListAdmin

from company.models.Employees import Availability
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(Availability)
class AvailabilityAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = (
        "employee__email",
        "availability_status",
        # "date_of_change"
        "travel_time"
    )
    autocomplete_fields = ("employee",)
    list_display_links = ("updated_at",)

    list_display = (
        "updated_at",
        "employee",
        "availability_status",
        "location_state",
        "location_city",
        # "date_of_change",
        "travel_time",
        "date_of_expected_future_change",
        "notes",
        # "modified_by",
    )
    list_editable = (
        "location_state",
        "location_city",
        "availability_status",
    )
    ordering = ("-updated_at",)

    fields = (
        "employee",
        "availability_status",
        "location_state",
        "location_city",
        # "date_of_change",
        "travel_time",
        "date_of_expected_future_change",
        "notes",
        ("updated_at", "modified_by",)
    )
    readonly_fields = (
        # "employee",
        "updated_at",
        "modified_by",
    )

    list_filter = (
        "availability_status",
        # "date_of_change",
        "travel_time",
        "date_of_expected_future_change",
        "location_state",
        "location_city",
    )
