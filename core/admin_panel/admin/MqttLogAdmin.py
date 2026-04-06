from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from core.models import Mqtt_Log


@admin.register(Mqtt_Log)
class MqttLogAdmin(FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    # list_display_links = ("updated_at",)

    list_per_page = 500
    search_fields = ()
    # autocomplete_fields = ("equipment_group",)

    list_display = (
        # "__str__",
        "updated_at",
        "topic",
        "phone",
        "beacon",
        "raw_data",
        "parsed_data",
        "condition_content",
        "raw_timestamp",
        "timestamp",
        "status",
        "error",
    )
    list_editable = (
        "status",
    )
    ordering = ("-updated_at",)

    fields = (
        "topic",
        "phone",
        "beacon",
        "raw_data",
        "parsed_data",
        "condition_content",
        "raw_timestamp",
        "timestamp",
        "status",
        "error",
        "updated_at",
    )
    readonly_fields = (
        "topic",
        "phone",
        "beacon",
        "raw_data",
        "parsed_data",
        "condition_content",
        "raw_timestamp",
        "timestamp",
        "status",
        "error",
        "updated_at",
    )

    list_filter = ("topic", "phone", "beacon", "timestamp", "updated_at",)
