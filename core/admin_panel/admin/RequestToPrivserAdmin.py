from django.contrib import admin
from django.utils.html import format_html
from django_admin_flexlist import FlexListAdmin

from privser.models import Request_To_Privser


@admin.register(Request_To_Privser)
class RequestToPrivserAdmin(FlexListAdmin):
    def has_add_permission(self, request):
        return False

    @admin.display(description="Execute")
    def execute_link(self, obj):
        return format_html(
            '<a class="button" style="background: var(--delete-button-bg);" href="/request/to/privser/{}">Execute</a>',
            obj.id
        )

    search_fields = ("contacts__email",)
    list_display = (
        "id",
        "contacts",
        "changed_properties",
        "errors",
        "status_code",
        "updated_at",
        "execute_link",
    )
    ordering = ("-updated_at",)

    fields = (
        "contacts",
        "changed_properties",
        "response_privser",
        "errors",
        "status_code",
        ("created_at", "updated_at")
    )
    readonly_fields = (
        "contacts",
        "changed_properties",
        "response_privser",
        "errors",
        "created_at",
        "updated_at",
    )

    list_filter = ("status_code",)
