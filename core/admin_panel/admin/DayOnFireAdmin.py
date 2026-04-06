from dalf.admin import DALFRelatedFieldAjax, DALFModelAdmin
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.template.response import TemplateResponse
from django_admin_flexlist import FlexListAdmin
from import_export.admin import ExportActionModelAdmin

from company.models.Employees import DayOnFire
from pdf_plugin.admin_mixin import PDFGenerateMixin
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone


@admin.register(DayOnFire)
class DayOnFireAdmin(PDFGenerateMixin, FlexListAdmin, ExportActionModelAdmin, DALFModelAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    def save_model(self, request, obj, form, change):
        def _aware(dt):
            if dt is None:
                return None
            return dt if not timezone.is_naive(dt) else timezone.make_aware(dt, timezone.get_current_timezone())

        total_seconds = 0
        for tin, tout in ((obj.clockin1, obj.clockout1), (obj.clockin2, obj.clockout2)):
            tin = _aware(tin)
            tout = _aware(tout)
            if tin and tout and tout > tin:
                total_seconds += (tout - tin).total_seconds()

        if total_seconds > 0:
            obj.hours_per_day = Decimal(total_seconds / 3600).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            obj.hours_per_day = None  # или Decimal("0.00"), если хочешь 0

        super().save_model(request, obj, form, change)

    def changelist_view(self, request, extra_context=None):
        resp = super().changelist_view(request, extra_context=extra_context)

        # Подменяем шаблон ТОЛЬКО для страницы списка (а не для confirm-delete, результатов действий и т.п.)
        if isinstance(resp, TemplateResponse):
            ctx = getattr(resp, "context_data", None) or {}
            cl = ctx.get("cl")
            if isinstance(cl, ChangeList):
                resp.template_name = "django_admin_flexlist/change_list.html"
                if getattr(resp, "template_name_list", None) is not None:
                    resp.template_name_list = ["django_admin_flexlist/change_list.html"]
        return resp

    autocomplete_fields = ("fire_run",)

    list_per_page = 50
    search_fields = (
        "fire_run__crew__c_number",
        "fire_run__crew__fire__fire_number",
        "fire_run__crew__fire__incident_name"
    )
    list_filter = (
        "job_title",
        ("fire_run", DALFRelatedFieldAjax),
    )
    list_display = (
        # "updated_at",
        "date",
        "fire_run",
        "crew_time_report",
        "job_title",
        "hours_per_day",
        "hotline_in_remarks",
        "operational_periods",
        "document_preview",
        # "modified_by",
    )
    list_editable = (
        # "fire_run",
        # "crew_time_report",
        # "job_title",
        # "hours_per_day",
    )
    ordering = ("-date",)

    fields = (
        "fire_run",
        "crew_time_report",
        "job_title",
        "date",
        "clockin1",
        "clockout1",
        "clockin2",
        "clockout2",
        "hours_per_day",
        "hotline_in_remarks",
        "operational_periods",
        "document",
        "document_preview",
        ("updated_at", "modified_by",)
    )
    readonly_fields = (
        "document_preview",
        "updated_at",
        "modified_by",
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
