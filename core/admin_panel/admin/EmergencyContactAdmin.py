from django.contrib import admin
from django_admin_flexlist import FlexListAdmin

from company.models.Employees import EmergencyContact


@admin.register(EmergencyContact)
class EmergencyContactAdmin(FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("employee__email",)
    autocomplete_fields = ("employee",)
    list_display = (
        "updated_at",
        "employee",
        "type",
        "relation_to_you",
        "is_primary",
        "relationship",
        # "modified_by",
    )
    list_editable = (
        "type",
        "relation_to_you",
        "is_primary",
    )
    ordering = ("-updated_at",)

    fields = (
        "employee",
        "type",
        "relation_to_you",
        "is_primary",
        "relationship",
        "updated_at",
        "modified_by",
    )
    readonly_fields = (
        # "employee",
        "updated_at",
        "modified_by",
    )

    list_filter = ()
