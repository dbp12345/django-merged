from django.contrib import admin
from django_admin_flexlist import FlexListAdmin

from privser.models import Request_From_Privser

@admin.register(Request_From_Privser)
class RequestFromPrivserAdmin(FlexListAdmin):
    def has_add_permission(self, request):
        return False

    list_per_page = 100
    search_fields = ("email",)
    list_display = (
        "id",
        "email",
        # "request",
        "errors",
        "updated",
        "status_code",
    )
    ordering = ("-updated",)

    list_editable = ("status_code",)

    fields = (
        "id",
        # "email",
        "request",
        "errors",
        "critical",
        ("created", "updated"),
        "status_code",
    )
    readonly_fields = (
        "id",
        "email",
        "request",
        "created",
        "updated"
    )

    # list_filter = ("status_code", "email")
    list_filter = ("status_code",)
