from django.urls import reverse
from django.utils.html import format_html
from django.contrib import admin
from django_admin_flexlist import FlexListAdmin

from privser.models import Custom_Fields

@admin.register(Custom_Fields)
class CustomFieldsAdmin(FlexListAdmin):


    # actions = ("update_fields")
    # def update_fields(self, request, queryset):
    #     privser_service = PrivserService()
    #     privser_service.update_custom_fields_in_db()
    #     for obj in queryset:
    #         obj.my_custom_function()
    #     self.message_user(request, "Fields updated.")
    #
    # update_fields.short_description = "Update fields from Privser"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['custom_button'] = format_html(
            '<a class="button" href="{}">Update fields from Privser</a>',
            reverse('update_fields_from_privser')
        )
        return super().changelist_view(request, extra_context=extra_context)

    list_per_page = 100
    autocomplete_fields = ("exchange_property",)
    search_fields = ("privser_id", "privser_name", "exchange_property__property_name")
    list_display = (
        "privser_name",
        "exchange_property",
        "privser_dataType",
        "no_sync",
        "main_field",
        # "date_time_format",
        "updated_at",
    )
    ordering = ("privser_name",)

    list_editable = ("exchange_property", "no_sync")

    fields = (
        "privser_id",
        "privser_name",
        "exchange_property",
        "no_sync",
        "main_field",
        "privser_fieldKey",
        "privser_placeholder",
        "privser_dataType",
        ("created_at", "updated_at")
    )
    readonly_fields = (
        "privser_id",
        # "privser_name",
        # "main_field",
        "privser_fieldKey",
        "privser_placeholder",
        "privser_dataType",
        "created_at",
        "updated_at",
    )



    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False