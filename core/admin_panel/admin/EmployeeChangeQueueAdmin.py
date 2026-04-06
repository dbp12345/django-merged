from django.contrib import admin
from django.db.models import Count
from django_admin_flexlist import FlexListAdmin

from company.models import Employee_Change_Queue

class StatusCodeFilter(admin.SimpleListFilter):
    title = "Status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        statuses = Employee_Change_Queue.objects.values("status").annotate(count=Count("status"))
        return [
            (status["status"], f"{Employee_Change_Queue.StatusCode(status['status']).label} ({status['count']})")
            for status in statuses
        ]

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(status=self.value())
        return queryset

@admin.register(Employee_Change_Queue)
class EmployeeChangeQueueAdmin(FlexListAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    list_display = (
        "id",
        "employee",
        "employee__email",
        "contacts_prop",
        "new_value",
        "status",
        # "error_message",
        "created_at",
        "updated_at",
    )
    list_editable = ("status",)
    list_filter = (StatusCodeFilter, "contacts_prop", "created_at")
    search_fields = ("employee__id", "employee__email", "contacts_prop__property_name", "new_value")
    ordering = ("-updated_at",)

    fields = (
        "employee",
        "contacts_prop",
        "new_value",
        "status",
        "error_message",
        ("created_at", "updated_at"),
    )
    readonly_fields = (
        "employee",
        "contacts_prop",
        "new_value",
        "created_at",
        "updated_at"
    )
