from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import Notes


@admin.register(Notes)
class NotesAdmin(FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("employee__email", "body")
    autocomplete_fields = ("employee",)
    list_display = (
        "updated_at",
        "employee",
        "body",
    )
    list_editable = (
        "body",
    )
    ordering = ("-updated_at", )

    fields = (
        "employee",
        "body",
        "updated_at",
        "modified_by",
    )
    readonly_fields = (
        "updated_at",
        "modified_by",
    )

    list_filter = ()
