from urllib.parse import urlencode

from django.contrib import admin
from django.urls import reverse, path
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django_admin_flexlist import FlexListAdmin

from company.models.Employees import FireCrew, FireCrewHistory
from dispatch.models import Dispatch
from pdf_plugin.admin_mixin import PDFGenerateMixin


class FireCrewHistoryInline(admin.TabularInline):
    model = FireCrewHistory
    extra = 0
    can_delete = False
    verbose_name_plural = "History"
    show_change_link = False

    list_display = (
        "updated_at",
        "employee",
        "modified_by",
        "action",
    )
    readonly_fields = (
        "action",
        "employee",
        "modified_by",
        "updated_at",
    )

    ordering = ("-updated_at",)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(FireCrew)
class FireCrewAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    @admin.display(description="Cards")
    def card_link(self, instance):
        if instance.pk:
            url = reverse("cards_crew_create") + "?" + urlencode({"crew": instance.pk})
            return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "cards")
        return "-"

    @admin.display(description="JSON")
    def json_link(self, instance):
        if not instance.pk:
            return "-"
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        url = reverse(f"admin:{app_label}_{model_name}_download_json", args=[instance.pk])
        return format_html('<a href="{}" download>json</a>', url)

    list_per_page = 100
    search_fields = ("employees__email", "name")

    autocomplete_fields = ("crew_boss",)

    list_display = (
        "updated_at",
        "name",
        "crew_boss",
        "employee_list",
        "employee_count",
        "card_link",
        "json_link",
        "group",
        "visible",
        # "modified_by",
    )
    list_editable = (
        "group",
        "visible",
        "name",
        "crew_boss",
    )
    ordering = ("-updated_at",)

    readonly_fields = (
        # "crew_boss",
        "updated_at",
        "modified_by",
        "employees_display",
    )

    list_filter = ("name", "group", "visible",)
    inlines = (FireCrewHistoryInline,)

    @admin.display(description="Employees")
    def employee_count(self, obj):
        return obj.employees.count()

    @admin.display(description="Employee Emails")
    def employee_list(self, obj):
        return format_html(
            "<ul style='margin: 0; padding-left: 1.2em; list-style-type: none;'>{}</ul>",
            format_html_join("", "<li>{}</li>", ((str(i.get_param_value("Email")),) for i in obj.employees.all()))
        )

    @admin.display(description="Employees in this crew")
    def employees_display(self, obj):
        employees = obj.employees.all()
        if not employees:
            return "No employees assigned"
        employee_links = [
            (
                f'<a href="/admin/company/employees/{employee.id}/change/" '
                f'target="_blank" rel="noreferrer noopener">{employee.get_param_value("Email")}</a>'
            )
            for employee in employees
        ]
        return mark_safe("<br>".join(employee_links))

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (None, {
                "fields": ("name", "crew_boss", "group", "visible", "updated_at", "modified_by")
            }),
        ]
        if obj:
            fieldsets.append(("Employees", {"fields": ("employees_display",)}))
        return fieldsets

    def get_urls(self):
        urls = super().get_urls()
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        custom = [
            path(
                "<int:pk>/download-json/",
                self.admin_site.admin_view(self.download_json),
                name=f"{app_label}_{model_name}_download_json",
            ),
        ]
        return custom + urls

    def download_json(self, request, pk: int):
        obj = get_object_or_404(self.model, pk=pk)
        latest_dispatch = (
            Dispatch.objects
            .filter(crew=obj)
            .select_related("fire")
            .order_by("-updated_at")
            .first()
        )

        # Build JSON payload. Keep keys you mentioned; add more later as needed.
        def safe_get(o, attr, default=None):
            return getattr(o, attr, default)

        employees_payload = []
        for e in obj.employees.all():
            employees_payload.append({
                "file_as": safe_get(e, "get_file_as"),      # may be None if field not present
                "email": safe_get(e, "get_email"),  # may be None if field not present
                "job_title": safe_get(e, "get_job_title"),  # may be None if field not present
            })

        data = {
            "crew_name": obj.name,
            "crew_boss": safe_get(obj.crew_boss, "get_file_as") if getattr(obj, "crew_boss", None) else None,
            "dispatch": {
                "ec_number": latest_dispatch.ec_number if latest_dispatch else None,
            },
            "fire": {
                "str": str(latest_dispatch.fire) if latest_dispatch else None,
            },
            "employees": employees_payload,
        }

        resp = JsonResponse(data, json_dumps_params={"ensure_ascii": False, "indent": 2})
        resp["Content-Disposition"] = f'attachment; filename="crew_{obj.name}.json"'
        return resp
