from django.contrib import admin
from django_admin_flexlist import FlexListAdmin

from core.models import Cron_Logs

@admin.register(Cron_Logs)
class CronLogsAdmin(FlexListAdmin):
    def has_add_permission(self, request):
        return False

    search_fields = ("body",)
    list_display = (
        "body",
    )
    ordering = ("-id",)

    fields = (
        "body",
    )
    readonly_fields = (
        "updated_at",
    )

    # list_filter = ("status_code", "email")
