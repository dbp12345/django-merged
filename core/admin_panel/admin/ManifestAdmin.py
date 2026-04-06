from django.contrib import admin
from datetime import timedelta
from django.utils.timezone import now
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import CompanyManifest
from pdf_plugin.admin_mixin import PDFGenerateMixin


class Last12MonthsFilter(admin.SimpleListFilter):
    title = "Last 12 months"
    parameter_name = "last_12_months"

    def lookups(self, request, model_admin):
        return [
            ("yes", "Last 12 months"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            twelve_months_ago = now().date() - timedelta(days=365)
            return queryset.filter(date__gte=twelve_months_ago)
        return queryset


@admin.register(CompanyManifest)
class ManifestAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("employee__email", "date",)
    autocomplete_fields = ("employee",)
    list_display_links = ("updated_at",)

    list_display = (
        "updated_at",
        "employee",
        "date",
    )
    list_editable = (
        "date",
    )
    ordering = ("-updated_at",)

    fields = (
        "employee",
        "date",
        "updated_at",
        "modified_by",
    )
    readonly_fields = (
        "updated_at",
        "modified_by",
    )

    list_filter = ("date", Last12MonthsFilter)
