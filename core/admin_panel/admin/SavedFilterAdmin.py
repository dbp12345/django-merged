from django.contrib import admin
# from django.utils.html import format_html
from django_admin_flexlist import FlexListAdmin

from core.models import Saved_Filter


@admin.register(Saved_Filter)
class SavedFilterAdmin(FlexListAdmin):
    list_display_links = None

    def has_add_permission(self, request):
        return False

    list_per_page = 50
    search_fields = ("name", "params", "columns")

    # @admin.display(description="columns")
    # def clickable_columns(self, obj):
    #     return format_html(
    #         '<a href="#" class="open-advanced-settings" data-id="{}">{}</a>',
    #         obj.pk, obj.columns,
    #     )

    list_display = (
        "name",
        # "clickable_columns",
        "order",
        # "columns",
        "dashboard",
    )
    list_editable = (
        "name",
        "order",
        "dashboard",
    )
    ordering = ("-dashboard", "order",)

    fields = (
        "name",
        "order",
        # "columns",
        "dashboard",
    )
    readonly_fields = ()

    list_filter = ("name", "order", "dashboard")

    class Media:
        css = {
            "all": (
                "core/custom_styles.css",
                # "grappelli/css/admin_breadcrumbs.css",
            )
        }
        js = (
            # "grappelli/js/admin_breadcrumbs.js",
        )
