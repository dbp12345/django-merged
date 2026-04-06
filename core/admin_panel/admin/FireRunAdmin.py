from dalf.admin import DALFModelAdmin, DALFRelatedFieldAjax
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.template.response import TemplateResponse
from django_admin_flexlist import FlexListAdmin
from import_export.admin import ExportActionModelAdmin
from import_export import resources, fields
from import_export.formats import base_formats
from more_admin_filters import MultiSelectDropdownFilter
from rangefilter.filters import DateRangeFilter
from company.models.Employees import FireRun, DayOnFire
from dispatch.models import Dispatch
from pdf_plugin.admin_mixin import PDFGenerateMixin


class DispatchStatusFilter(admin.SimpleListFilter):
    title = "Dispatch status"
    parameter_name = "dispatch_status"

    def lookups(self, request, model_admin):
        return [(k, v) for k, v in Dispatch._meta.get_field("status").choices if k]

    def queryset(self, request, queryset):
        val = self.value()
        if not val:
            return queryset
        return queryset.filter(crew__fire__dispatch_entries__status=val).distinct()


class TaskBookFilter(admin.SimpleListFilter):
    title = "Task Book"
    parameter_name = "has_task_book"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Has Task Book"),
            ("no", "No Task Book"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(task_book__isnull=False)
        elif self.value() == "no":
            return queryset.filter(task_book__isnull=True)
        return queryset


class FireRunResource(resources.ModelResource):
    firefighter_name = fields.Field(column_name="Firefighter Name")
    job_code = fields.Field(column_name="Job Code")
    activity_code = fields.Field(column_name="Activity Code (WF)")
    start_date = fields.Field(column_name="Start Date")
    agency = fields.Field(column_name="Agency")
    state = fields.Field(column_name="State")
    operational_periods = fields.Field(column_name="Oper. periods")
    incident_type = fields.Field(column_name="Incident Type")
    fuel_type = fields.Field(column_name="Fuel Type 1-4")
    fire_size = fields.Field(column_name="Fire Size A, B, C, D, E, F, G")
    incident_name = fields.Field(column_name="Incident Name")
    incident_type_dup = fields.Field(column_name="Incident Type")
    agency_ask_chris = fields.Field(column_name="Agency")
    state_dup = fields.Field(column_name="State")
    operational_dup = fields.Field(column_name="Operational")
    month_year = fields.Field(column_name="Month/Year")
    hotline_shifts = fields.Field(column_name="Hotline shifts")
    fire_number = fields.Field(column_name="Fire Number boxg")
    eval_hotline = fields.Field(column_name="Eval Hotline?")
    hotline_in_remarks = fields.Field(column_name="Hotline in Remarks")
    total_shift = fields.Field(column_name="Total shift")
    crew_boss = fields.Field(column_name="Crew Boss")
    contract_number = fields.Field(column_name="Contract Number boxA")
    crew_number = fields.Field(column_name="Crew Number")
    rating = fields.Field(column_name="Rating")
    ranking = fields.Field(column_name="Ranking")

    class Meta:
        model = FireRun
        fields = (
            "firefighter_name",  # Firefighter Name
            "job_code",  # Job Code
            "activity_code",  # Activity Code (WF)
            "start_date",  # Start Date
            "agency",  # Agency
            "state",  # State
            "operational_periods",  # Operational Periods
            "incident_type",  # Incident Type
            "fuel_type",  # Fuel Type 1-4
            "fire_size",  # Fire Size A, B, C, D, E, F, G
            "incident_name",  # Incident Name
            "incident_type_dup",  # Incident Type
            "agency_ask_chris",  # Agency ask chris,
            "state_dup",  # State
            "operational_dup",  # Operational Periods
            "month_year",  # Month/Year
            "hotline_shifts",  # Hotline Shifts
            "fire_number",  # Fire Number box9
            "eval_hotline",  # Eval Hotline? (B/LC/HL/NA)
            "hotline_in_remarks",  # Hotline in Remarks? (Y/N)
            "total_shift",  # Total Shift Tickets
            "crew_boss",  # Crew Boss
            "contract_number",  # Contract Number box4
            "crew_number",  # Crew Number
            "rating",  # Rating
            "ranking",  # Ranking
        )
        export_order = fields

    # ---- Заготовки значений ----
    def dehydrate_firefighter_name(self, obj):
        return obj.employee.get_file_as if obj.employee else None
        # return (
        #         getattr(emp, "get_file_as", None)
        #         or obj.firefighter_name
        #         or getattr(emp, "get_email", None)
        #         or (emp.email if emp else "")
        # )

    def dehydrate_job_code(self, obj):
        return obj.job_title
        # return getattr(obj, "get_job_title_display", lambda: obj.job_title or "")()

    def dehydrate_activity_code(self, obj):
        return "WF"

    def dehydrate_start_date(self, obj):
        return obj.start_date.strftime("%m/%d/%Y") if obj.start_date else ""
        # return obj.start_date or ""

    def dehydrate_agency(self, obj):
        fire = obj.crew.fire if obj.crew and obj.crew.fire_id else None
        return (fire.agency if fire else "") or ""

    def dehydrate_state(self, obj):
        fire = obj.crew.fire if obj.crew and obj.crew.fire_id else None
        return (fire.state if fire else "") or ""

    def dehydrate_operational_periods(self, obj):
        return obj.operational_periods or ""

    def dehydrate_incident_type(self, obj):
        fire = obj.crew.fire if obj.crew and obj.crew.fire_id else None
        return (fire.incident_type if fire else "") or ""

    def dehydrate_fuel_type(self, obj):
        fire = obj.crew.fire if obj.crew and obj.crew.fire_id else None
        return (fire.fuel_type if fire and fire.fuel_type else obj.fuel_type) or ""

    def dehydrate_fire_size(self, obj):
        fire = obj.crew.fire if obj.crew and obj.crew.fire_id else None
        return (fire.fire_size if fire and fire.fire_size else obj.fire_size) or ""

    def dehydrate_incident_name(self, obj):
        fire = obj.crew.fire if obj.crew and obj.crew.fire_id else None
        return (fire.incident_name if fire else "") or ""

    def dehydrate_agency_ask_chris(self, obj):
        return self.dehydrate_agency(obj)

    def dehydrate_state_dup(self, obj):
        return self.dehydrate_state(obj)

    def dehydrate_incident_type_dup(self, obj):
        return self.dehydrate_incident_type(obj)

    def dehydrate_operational_dup(self, obj):
        return self.dehydrate_operational_periods(obj)

    def dehydrate_month_year(self, obj):
        return obj.month_year or ""

    def dehydrate_hotline_shifts(self, obj):
        return obj.hotline_shifts or ""

    def dehydrate_fire_number(self, obj):
        fire = obj.crew.fire if obj.crew and obj.crew.fire_id else None
        return (fire.fire_number if fire else "") or ""

    def dehydrate_eval_hotline(self, obj):
        return (obj.eval_hotline or "").strip()
        # val = (obj.eval_hotline or "").strip()
        # if not val:
        #     return ""
        # return "Y" if val.lower().startswith("y") else val

    def dehydrate_hotline_in_remarks(self, obj):
        return "Y" if bool(obj.hotline_in_remarks) else "N"

    def dehydrate_total_shift(self, obj):
        return obj.total_shift_tickets or ""

    def dehydrate_crew_boss(self, obj):
        # crew = obj.crew
        # boss = crew.crew_boss if crew else None
        boss = obj.crwb
        if not boss:
            return ""
        return boss.get_file_as
        # return boss.get_file_as or boss.get_email or boss.email or ""

    def dehydrate_contract_number(self, obj):
        crew = obj.crew
        return crew.contract if crew else ""

    def dehydrate_crew_number(self, obj):
        crew = obj.crew
        return crew.c_number if crew else ""

    def dehydrate_rating(self, obj):
        return obj.rating or ""

    def dehydrate_ranking(self, obj):
        return obj.ranking or ""


class DayOnFireInline(admin.TabularInline):
    model = DayOnFire
    fields = (
        # "updated_at_link",
        "date",
        "fire_run",
        "crew_time_report",
        "job_title",
        # "clockin1",
        # "clockout1",
        # "clockin2",
        # "clockout2",
        "hotline_in_remarks",
        "operational_periods",
        "hours_per_day",
        "document_preview",
    )
    readonly_fields = (
        "document_preview",
        # "updated_at_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("date",)

    # @admin.display(description="Updated At")
    # def updated_at_link(self, instance):
    #     url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name),
    #  args=[instance.id])
    #     return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>',
    #  url, instance.updated_at.strftime('%m/%d/%Y %H:%M'))


@admin.register(FireRun)
class FireRunAdmin(PDFGenerateMixin, FlexListAdmin, ExportActionModelAdmin, DALFModelAdmin):
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

    resource_class = FireRunResource
    formats = (base_formats.CSV, base_formats.XLSX)

    def get_export_filename(self, request, queryset, file_format):
        # CHANGED: stable, readable filename
        from django.utils import timezone
        ts = timezone.now().strftime("%Y-%m-%d-%H-%M-%S")
        return f"fire_run-{ts}.{file_format.get_extension()}"

    list_per_page = 100

    search_fields = ("employee__email", "crew__fire__fire_number", "crew__c_number", "crew__fire__incident_name",)
    list_filter = (
        ("crew", DALFRelatedFieldAjax),
        ("crwb", DALFRelatedFieldAjax),
        ("task_book", DALFRelatedFieldAjax),
        TaskBookFilter,
        ("employee", DALFRelatedFieldAjax),
        ("job_title", MultiSelectDropdownFilter),
        DispatchStatusFilter,
        ("start_date", DateRangeFilter),
    )

    autocomplete_fields = ("employee", "crwb", "task_book", "crew")
    # raw_id_fields = ("employee", "crwb", "crew")

    # #TO-DO
    # @admin.display(description="Rating emp")
    # def rating_from_emp(self, obj):
    #     if obj.employee:
    #         return obj.employee.get_param_value("Rating")
    #     return ""
    #
    # #TO-DO
    # @admin.display(description="Ranking emp")
    # def ranking_from_emp(self, obj):
    #     if obj.employee:
    #         return obj.employee.get_param_value("Ranking 1 to 10")
    #     return ""

    list_display = (
        "__str__",
        "employee",
        "job_title",
        # "firefighter_name",
        "crwb",
        "task_book",
        "start_date",
        "total_shift_tickets",
        "operational_periods",
        "activity_code",
        "fuel_type",
        "fire_size",
        "eval_hotline",
        "hotline_in_remarks",
        "crew",
        "CRWB_potential",
        # "rating_from_emp",#TO-DO
        "rating",
        # "ranking_from_emp",#TO-DO
        "ranking",
        "professionalism_rating",
        "attitude_rating",
        "sawyer_rating",
        # "month_year",
        "hotline_shifts",
        # "created_at",
        # "modified_by",
    )
    list_editable = (
        # "crew",
        "employee",
        "job_title",
        # "firefighter_name",
        "crwb",
        "task_book",
        "start_date",
        "total_shift_tickets",
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
    ordering = ("-start_date",)

    fields = (
        "employee",
        "job_title",
        # "firefighter_name",
        "start_date",
        "crwb",
        "task_book",
        "total_shift_tickets",
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
        ("updated_at",
         "modified_by"),
    )
    readonly_fields = (
        "updated_at",
        "modified_by",
    )

    inlines = (
        DayOnFireInline,
    )

    class Media:
        css = {
            "all": (
                "core/DALFRelatedFieldAjax.css",
                "core/fire_run_admin.css",
                # "grappelli/css/admin_breadcrumbs.css",
            )
        }
        js = (
            # "grappelli/js/admin_breadcrumbs.js",
        )
