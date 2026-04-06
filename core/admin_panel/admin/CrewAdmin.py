from dalf.admin import DALFRelatedFieldAjax, DALFModelAdmin
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from django_admin_flexlist import FlexListAdmin

from company.models.Employees import Crew, FireRun, CrewTimeReport, Evaluation
from pdf_plugin.admin_mixin import PDFGenerateMixin


class FireRunInline(admin.TabularInline):
    model = FireRun
    autocomplete_fields = ("crew", "employee", "crwb",)
    fields = (
        # "updated_at_link",
        "employee",
        "job_title",
        "start_date",
        "total_shift_tickets",
        "crwb",
        "operational_periods",
        "activity_code",
        "fuel_type",
        "fire_size",
        "eval_hotline",
        "hotline_in_remarks",
        "crew",
        "CRWB_potential",
        "rating",
        "ranking",
        "professionalism_rating",
        "attitude_rating",
        "sawyer_rating",
        # "month_year",
        "hotline_shifts",
    )
    readonly_fields = (
        # "updated_at_link",
    )
    extra = 0
    show_change_link = True
    can_delete = True
    ordering = ("-start_date",)

    @admin.display(description="Updated At")
    def updated_at_link(self, instance):
        url = reverse(
            "admin:%s_%s_change"
            % (instance._meta.app_label, instance._meta.model_name),
            args=[instance.id],
        )
        return format_html(
            '<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>',
            url,
            instance.updated_at.strftime("%m/%d/%Y %H:%M"),
        )


class CrewTimeReportInline(admin.TabularInline):
    model = CrewTimeReport
    autocomplete_fields = ("crew",)
    fields = (
        "updated_at_link",
        "crew",
        "hotline_in_remarks",
        "document",
        "document_preview",
    )
    readonly_fields = (
        "updated_at_link",
        "document_preview",
    )
    extra = 0
    can_delete = True
    ordering = ("-id",)

    @admin.display(description="Updated At")
    def updated_at_link(self, instance):
        url = reverse(
            "admin:%s_%s_change"
            % (instance._meta.app_label, instance._meta.model_name),
            args=[instance.id],
        )
        return format_html(
            '<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>',
            url,
            instance.updated_at.strftime("%m/%d/%Y %H:%M"),
        )


class EvaluationInline(admin.TabularInline):
    model = Evaluation
    autocomplete_fields = ("crew",)
    fields = (
        "updated_at_link",
        "crew",
        "rated_by",
        "date",
        "hotline",
        "document",
        "document_preview",
    )
    readonly_fields = (
        "updated_at_link",
        "document_preview",
    )
    extra = 0
    can_delete = True
    ordering = ("-id",)

    @admin.display(description="Updated At")
    def updated_at_link(self, instance):
        url = reverse(
            "admin:%s_%s_change"
            % (instance._meta.app_label, instance._meta.model_name),
            args=[instance.id],
        )
        return format_html(
            '<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>',
            url,
            instance.updated_at.strftime("%m/%d/%Y %H:%M"),
        )


@admin.register(Crew)
class CrewAdmin(PDFGenerateMixin, FlexListAdmin, DALFModelAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = ("crew_name", "fire__incident_name", "c_number", "fire__fire_number", "dispatch__ec_number",)
    # list_filter = ("fire", "fire__incident_name", "c_number", "fire__fire_number")
    list_filter = (
        "crew_name",
        "c_number",
        ("fire", DALFRelatedFieldAjax),
        ("dispatch", DALFRelatedFieldAjax),
    )
    list_select_related = ("fire",)
    autocomplete_fields = ("fire", "crew_boss")

    @admin.display(description="")
    def filter_list_by_crew_name(self, instance):
        url = reverse("admin:company_crew_changelist")
        query = urlencode({"q": f"{instance.crew_name}"})
        full_url = f"{url}?{query}"
        return format_html('<a href="{}" rel="noreferrer noopener">filter</a>', full_url)

    list_display = (
        "__str__",
        "crew_name",
        # "crew_boss",
        "fire",
        "dispatch",
        "c_number",
        "contract",
        # "created_at",
        # "modified_by",
    )
    list_editable = (
        # "fire",
        # "dispatch",
        "crew_name",
        # "crew_boss",
        "c_number",
        "contract",
    )
    ordering = ()

    fields = (
        ("crew_name", "filter_list_by_crew_name"),
        # "crew_boss",
        "fire",
        "dispatch",
        "c_number",
        "contract",
        ("updated_at",
         "modified_by")
    )
    readonly_fields = (
        "filter_list_by_crew_name",
        "updated_at",
        "modified_by",
    )

    inlines = (
        FireRunInline,
        CrewTimeReportInline,
        EvaluationInline,
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
