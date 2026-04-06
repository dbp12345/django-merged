from django.contrib import admin
from django_admin_flexlist import FlexListAdmin

from exchange.models import Contacts_Prop


@admin.register(Contacts_Prop)
class ContactsPropAdmin(FlexListAdmin):
    list_per_page = 100
    search_fields = ("property_name",)
    list_display = (
        "property_name",
        "property_type",
        "datetime_format",
        # "property_tag",
        # "property_set_id",
        "visibility",
    )
    ordering = ("property_name",)

    list_editable = ("visibility",)

    fields = (
        "property_name",
        "property_type",
        "datetime_format",
        # "property_tag",
        # "property_set_id",
        "visibility",
        "updated_at"
    )
    readonly_fields = (
        "updated_at",
    )

    # list_filter = ("status_code", "email")
    list_filter = ("visibility", "property_type")
