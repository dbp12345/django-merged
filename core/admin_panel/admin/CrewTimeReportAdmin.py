from dalf.admin import DALFRelatedFieldAjax, DALFModelAdmin
from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import CrewTimeReport, DayOnFire
from pdf_plugin.admin_mixin import PDFGenerateMixin


class DayOnFireInline(admin.TabularInline):
    model = DayOnFire
    fields = (
        "id",
        "fire_run",
        "crew_time_report",
        "job_title",
        "clockin1",
        "clockout1",
        "clockin2",
        "clockout2",
        "hours_per_day",
        "document",
        "document_preview",
    )
    readonly_fields = (
        "id",
        "document_preview",
    )
    extra = 0
    can_delete = True
    ordering = ("-id",)


@admin.register(CrewTimeReport)
class CrewTimeReportAdmin(PDFGenerateMixin, FlexListAdmin, DALFModelAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("crew__fire__fire_number", "crew__c_number", "crew__fire__incident_name",)
    list_filter = (
        ("crew", DALFRelatedFieldAjax),
    )
    autocomplete_fields = ("crew",)
    list_display = (
        "updated_at",
        "crew",
        "hotline_in_remarks",
        "document",
        "document_preview",
        # "modified_by",
    )
    list_editable = (
        "crew",
        "hotline_in_remarks",
        "document",
    )
    ordering = ()

    fields = (
        "crew",
        "hotline_in_remarks",
        "document",
        "document_preview",
        ("updated_at", "modified_by"),
    )
    readonly_fields = (
        "updated_at",
        "modified_by",
        "document_preview",
    )

    inlines = (
        DayOnFireInline,
    )

    class Media:
        css = {
            "all": (
                "core/DALFRelatedFieldAjax.css",
                # "grappelli/css/admin_breadcrumbs.css",
            )
        }
        js = (
            # "grappelli/js/admin_breadcrumbs.js",
        )
