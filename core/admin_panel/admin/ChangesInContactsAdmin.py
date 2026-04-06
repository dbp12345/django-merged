"""
from django.contrib import admin
from django.utils.html import format_html
from company.models import Employees_Parameters
# from exchange.models.Contacts import ChangesInContacts

class ContactsParametersInline(admin.TabularInline):  #admin.StackedInline
    def has_add_permission(self, request, obj=None):
        return False

    model = Employees_Parameters
    fields = (
        "contacts_parameters",
        "value",
        "updated_at",
    )
    readonly_fields = (
        "contacts_parameters",
        "value",
        "updated_at",
    )
    extra = 0
    can_delete = False
    ordering = ("-updated_at",)

@admin.register(ChangesInContacts)
class ChangesInContactsAdmin(FlexListAdmin):

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(changed_properties__isnull=False).exclude(changed_properties={})

    def has_add_permission(self, request):
        return False

    def execute_link(self, obj):
        return format_html(
            '<a class="button" style="background: var(--delete-button-bg);" href="/create/request/to/privser/{}">Create</a>',
            obj.id
        )
    execute_link.short_description = "Create"

    inlines = (ContactsParametersInline,)

    list_per_page = 100
    search_fields = ("id", "email", "last_modified_name")
    list_display = (
        "email",
        "changed_properties",
        "last_modified_name",
        "last_modified_time",
        "status_code",
        "updated_at",
        "execute_link"
    )
    ordering = ("-last_modified_time",)

    list_editable = ("status_code",)

    fields = (
        # "email",
        "contact_id",
        "changed_properties",
        # "properties", -- удалить из системы
        "last_modified_name",
        "last_modified_time",
        "status_code",
        ("created_at", "updated_at")
    )
    readonly_fields = (
        "email",
        "contact_id",
        "last_modified_name",
        "last_modified_time",
        "created_at",
        "updated_at"
    )

    # list_filter = ("status_code", "email")
    list_filter = ("status_code",)
"""
