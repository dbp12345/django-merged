from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from django_admin_flexlist import FlexListAdmin

from synchronization.models import Sync_Parameters_Logs


class StatusCodeFilter(admin.SimpleListFilter):
    title = "Status"
    parameter_name = "status_code"

    def lookups(self, request, model_admin):
        statuses = Sync_Parameters_Logs.objects.values("status_code").annotate(count=Count("status_code"))
        return [
            (status["status_code"], f"{Sync_Parameters_Logs.StatusCode(status['status_code']).label} ({status['count']})")
            for status in statuses
        ]

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(status_code=self.value())
        return queryset


@admin.register(Sync_Parameters_Logs)
class SyncParametersLogsAdmin(FlexListAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Email")
    def short_email(self, obj):
        if len(obj.email) > 36:
            return f"{obj.email[:36]}..."
        return obj.email

    list_display = (
        "id",
        "short_email",
        "employee",
        "contact_privser",
        "property_name",
        "source_system",
        "target_system",
        "privser_custom_fields",
        "old_value",
        "new_value",
        "old_value_updated",
        "new_value_updated",
        "modified_by",
        "created_at",
        # "updated_at",
        "status_code",
        "body",
    )
    list_editable = ("status_code",)
    list_filter = (StatusCodeFilter, "source_system", "target_system", "created_at", "modified_by", "privser_custom_fields")
    search_fields = ("employee__id", "employee__email", "email", "contact_privser__email", "old_value", "new_value", "modified_by")
    ordering = ("-created_at",)

    @admin.display(description="")
    def execute_link(self, obj):
        url = reverse("sync_parameters_logs_execute", kwargs={"sync_parameters_logs_id": obj.id})
        return format_html(
            '<a class="button" style="background: var(--delete-button-bg);" href="{}">Execute</a>',
            url
        )

    fields = (
        (
            "email",
            "employee",
            "contact_privser",
            "execute_link",
        ),
        "privser_custom_fields",
        (
            "source_system",
            "target_system",
        ),
        (
            "property_name",
            "old_value",
            "new_value",
        ),
        (
            "old_value_updated",
            "new_value_updated",
        ),
        (
            "created_at", "updated_at"
        ),
        ("status_code", "modified_by"),
        "body",
    )
    readonly_fields = (
        "execute_link",
        "email",
        "employee",
        "contact_privser",
        "privser_custom_fields",
        "source_system",
        "target_system",
        "property_name",
        "new_value",
        "old_value",
        "new_value_updated",
        "old_value_updated",
        "modified_by",
        "created_at",
        "updated_at"
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("employee", "contact_privser", "privser_custom_fields")
        status_filter = request.GET.get("status_code")
        if status_filter is None:
            queryset = queryset.exclude(status_code__in=[50])
        return queryset

    class Media:
        css = {
            "all": (
                "admin/css/sync_parameters_logs.css",
            )
        }
