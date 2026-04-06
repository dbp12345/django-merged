from django.contrib import admin
from django.utils.html import format_html
from django_admin_flexlist import FlexListAdmin

from privser.models import Contacts as ContactsPrivser, Contacts_Parameters


class ContactsParametersInline(admin.TabularInline):  # admin.StackedInline
    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Name")
    def custom_fields_name_and_privser_name(self, obj):
        return format_html("{}<br/>({})", obj.custom_fields_privser_name, obj.name)

    model = Contacts_Parameters
    fields = (
        # "name",
        # "custom_fields_privser_name",
        "custom_fields_name_and_privser_name",
        "value",
        "updated_at",
    )
    readonly_fields = (
        # "name",
        # "custom_fields_privser_name",
        "custom_fields_name_and_privser_name",
        "value",
        "updated_at",
    )
    extra = 0
    can_delete = False
    ordering = ("name",)


@admin.register(ContactsPrivser)
class ContactsPrivserAdmin(FlexListAdmin):
    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    # def execute_link(self, obj):
    #     return format_html(
    #         '<a class="button" style="background: var(--delete-button-bg);" href="/create/request/to/privser/{}">
    # Create</a>',
    #         obj.id
    #     )
    # execute_link.short_description = "Create"

    inlines = (ContactsParametersInline,)

    list_per_page = 100
    search_fields = ("id", "email", "contact_id")

    @admin.display(description="Refresh from Privser")
    def refresh_link_privser(self, obj):
        return format_html(
            (
                '<a class="button" style="background: var(--button-bg);" '
                'href="/admin/update/contact/from/privser/{}">'
                'Force PULL All</a>'
            ),
            obj.id,
        )

    # @admin.display(description="Email")
    # def short_email(self, obj):
    #     if len(obj.email) > 36:
    #         return f"{obj.email[:36]}..."
    #     return obj.email

    list_display = (
        "updated_at",
        "email",
        # "changed_properties",
        "last_activity",
        "date_updated",
        # "status_code",
        "refresh_link_privser",
        # "execute_link"
    )
    ordering = ("-updated_at",)

    # list_editable = ("status_code",)

    fields = (
        # "email",
        "contact_id",
        "refresh_link_privser",
        # "changed_properties",
        # "properties", -- удалить из системы
        "last_activity",
        "date_updated",
        # "status_code",
        ("created_at", "updated_at")
    )
    readonly_fields = (
        "email",
        "refresh_link_privser",
        "contact_id",
        "last_activity",
        "date_updated",
        "created_at",
        "updated_at"
    )

    # list_filter = ("status_code", "email")
    # list_filter = ("status_code",)
