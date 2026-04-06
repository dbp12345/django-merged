from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django_admin_flexlist import FlexListAdmin

from synchronization.models import Sync_Delivery_Logs


class StatusCodeFilter(admin.SimpleListFilter):
    title = "Status"
    parameter_name = "status_code"

    def lookups(self, request, model_admin):
        statuses = Sync_Delivery_Logs.objects.values("status_code").annotate(count=Count("status_code"))
        return [
            (status["status_code"], f"{Sync_Delivery_Logs.StatusCode(status['status_code']).label} ({status['count']})")
            for status in statuses
        ]

    def queryset(self, request, queryset):
        if self.value() is not None:
            return queryset.filter(status_code=self.value())
        return queryset


@admin.register(Sync_Delivery_Logs)
class SyncDeliveryLogsAdmin(FlexListAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = (
        "id",
        "email",
        "contacts_prop",
        "privser_custom_fields",
        "privser_custom_fields_name",
        "target_system",
        "old_value",
        "new_value",
        "modified_by",
        # "updated_at",
        "status_code",
        "created_at",
        "updated_at",
        "body",
    )
    list_editable = ("status_code",)
    list_filter = (StatusCodeFilter, "target_system", "created_at", "contacts_prop", "privser_custom_fields")
    search_fields = ("employee__id", "employee__email", "email", "contacts_prop__property_name")
    ordering = ("-created_at",)

    @admin.display(description="")
    def execute_link(self, obj):
        url = reverse("sync_delivery_logs_execute", kwargs={"sync_delivery_logs_id": obj.id})
        return format_html(
            '<a class="button" style="background: var(--delete-button-bg);" href="{}">Execute</a>',
            url
        )

    @admin.display(description="Body (formatted)")
    def formatted_body(self, obj):
        from pprint import pformat

        body = obj.body
        if not body:
            return "-"
        if isinstance(body, dict):
            body_str = pformat(body, width=250)
        else:
            body_str = str(body)

        return mark_safe(f"<pre style='white-space:pre-wrap'>{body_str}</pre>")

    fields = (
        (
            "email",
            "execute_link",
        ),
        "target_system",
        (
            "privser_custom_fields",
            "privser_custom_fields_name",
        ),
        (
            "contacts_prop",
            "old_value",
            "new_value",
        ),
        (
            "created_at", "updated_at"
        ),
        ("status_code", "modified_by"),
        "body",
        "formatted_body",
    )
    readonly_fields = (
        "execute_link",
        "email",
        "target_system",
        "privser_custom_fields",
        "privser_custom_fields_name",
        "contacts_prop",
        "new_value",
        "old_value",
        "modified_by",
        "created_at",
        "updated_at",
        "formatted_body",
    )

    class Media:
        css = {
            "all": (
                "admin/css/sync_parameters_logs.css",
            )
        }
