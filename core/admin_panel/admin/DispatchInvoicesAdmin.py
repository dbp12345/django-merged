import os

# from dalf.admin import DALFRelatedFieldAjax
from django.contrib import admin
from django.db.models import (
    Count, Prefetch, Sum, Value, DecimalField, F, OuterRef, Subquery, Case, When, ExpressionWrapper
)
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django_admin_flexlist import FlexListAdmin

from company.models import DayOnFire
from dispatch.models.Dispatch import DispatchInvoicesProxy
from dispatch.models import Invoice
from pdf_plugin.admin_mixin import PDFGenerateMixin


class HasInvoicesFilter(admin.SimpleListFilter):
    title = "Has invoices"
    parameter_name = "has_invoices"

    def lookups(self, request, model_admin):
        return (("1", "With invoices"), ("0", "Without invoices"))

    def queryset(self, request, queryset):
        queryset = queryset.annotate(_inv_cnt=Count("invoices_entries", distinct=True))
        if self.value() == "1":
            return queryset.filter(_inv_cnt__gt=0)
        if self.value() == "0":
            return queryset.filter(_inv_cnt=0)
        return queryset


@admin.register(DispatchInvoicesProxy)
class DispatchInvoicesAdmin(PDFGenerateMixin, FlexListAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = (
        "dispatch_title",
        "invoices_column",
        "status_finance",
        "payroll_run",
        "payroll_ready",
        "notes_finance",
        "invoice_total",
        "hours_day_on_fire",
        # "hours_day_on_fire_by_crew",
        # "dof_hours",           # by crew_id
        "estimated_hours",
        "invoice_difference",
        "estimated_hours_by_crew",
    )
    list_editable = (
        "payroll_run",
        "payroll_ready",
        "status_finance",
        "notes_finance",
    )
    list_per_page = 100

    search_fields = (
        "ec_number",
        "company",
        "status",
        # "fire__incident_name",  # uncomment if you want search by fire
        # "fire__fire_number",
        # "fire__state",
        "invoices_entries__invoice_number",
        "invoices_entries__status",
    )

    list_filter = (
        "company",
        "status",
        # ("first_operational_period", admin.DateFieldListFilter),  # keep if useful
        HasInvoicesFilter,
        "invoices_entries__status",
        "status_finance",
        # ("invoices_entries", DALFRelatedFieldAjax),  # CHANGED: enable if you want AJAX pick by Invoice
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        qs = (
            qs.select_related("crew", "fire", "contract")
              .prefetch_related(
                  Prefetch(
                      "invoices_entries",
                      queryset=Invoice.objects.only(
                          "id", "invoice_number", "invoice_amount", "status", "invoice_date", "file", "updated_at"
                      ).order_by("-updated_at")
                  )
              )
            # .annotate(_inv_cnt=Count("invoices_entries", distinct=True))  # CHANGED: for count sorting/filtering
        )

        zero_decimal = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))

        # total hours on the fire (all crews) — used to prorate estimated hours
        sub_total_fire = (
            DayOnFire.objects
            .filter(fire_run__crew__fire_id=OuterRef("fire_id"))
            .values("fire_run__crew__fire_id")
            .annotate(total=Coalesce(Sum("hours_per_day"), zero_decimal))
            .values("total")[:1]
        )

        # hours only for the crew that matches Dispatch.ec_number (Crew.c_number == Dispatch.ec_number)
        sub_hours_for_dispatch_crew = (
            DayOnFire.objects
            .filter(
                fire_run__crew__fire_id=OuterRef("fire_id"),
                fire_run__crew__c_number=OuterRef("ec_number"),
            )
            .values("fire_run__crew__c_number")
            .annotate(total=Coalesce(Sum("hours_per_day"), zero_decimal))
            .values("total")[:1]
        )

        # invoice total
        invoice_total_expr = Coalesce(Sum("invoices_entries__invoice_amount"), zero_decimal)

        qs = qs.annotate(
            _hours_day_on_fire=Subquery(sub_hours_for_dispatch_crew),
            _hours_total_fire=Subquery(sub_total_fire),
            _invoice_total=invoice_total_expr,
        )

        # estimated total hours for whole dispatch (invoice_total / per_dof_hr)
        est_total_expr = ExpressionWrapper(
            F("_invoice_total") / F("contract__per_dof_hr"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )

        # estimated hours for this crew = est_total * (crew_hours / total_fire_hours)
        est_for_crew_expr = ExpressionWrapper(
            est_total_expr * (F("_hours_day_on_fire") / F("_hours_total_fire")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )

        qs = qs.annotate(
            _estimated_hours=Case(
                When(contract__per_dof_hr__gt=0, _hours_total_fire__gt=0, then=est_for_crew_expr),
                default=Value(None),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )

        # invoice difference = estimated (for this crew) - actual (for this crew)
        diff_expr = ExpressionWrapper(
            F("_estimated_hours") - F("_hours_day_on_fire"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        qs = qs.annotate(
            _invoice_difference=Case(
                When(_estimated_hours__isnull=False, then=diff_expr),
                default=Value(None),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )

        return qs

    @admin.display(description="Hours (day on fire)", ordering="_hours_day_on_fire")
    def hours_day_on_fire(self, obj):
        return round(float(getattr(obj, "_hours_day_on_fire", 0) or 0), 2)

    @admin.display(description="Invoice total", ordering="_invoice_total")
    def invoice_total(self, obj):
        v = getattr(obj, "_invoice_total", None)
        return "" if v is None else round(float(v or 0), 2)

    @admin.display(description="Estimated hours", ordering="_estimated_hours")
    def estimated_hours(self, obj):
        v = getattr(obj, "_estimated_hours", None)
        return "" if v is None else round(float(v or 0), 2)

    @admin.display(description="Invoice difference", ordering="_invoice_difference")
    def invoice_difference(self, obj):
        v = getattr(obj, "_invoice_difference", None)
        return "" if v is None else round(float(v or 0), 2)

    @admin.display(description="Estimated hours by crew")
    def estimated_hours_by_crew(self, obj):
        zero_decimal = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))

        inv_total_raw = getattr(obj, "_invoice_total", None)
        try:
            inv_total = float(inv_total_raw) if inv_total_raw is not None else 0.0
        except Exception:
            inv_total = 0.0

        per_hr = None
        if getattr(obj, "contract", None):
            per_hr_raw = getattr(obj.contract, "per_dof_hr", None)
            try:
                per_hr = float(per_hr_raw) if per_hr_raw is not None else None
            except Exception:
                per_hr = None

        if per_hr is None or per_hr == 0:
            return "-"

        total_est = inv_total / per_hr

        qs = (
            DayOnFire.objects
            .filter(fire_run__crew__fire_id=obj.fire_id)
            .values("fire_run__crew__c_number", "fire_run__crew__id")
            .annotate(total=Coalesce(Sum("hours_per_day"), zero_decimal))
            .order_by("fire_run__crew__c_number")
        )

        # build list of (crew_code, hours) preserving available data
        items = []
        for r in qs:
            crew_code = r.get("fire_run__crew__c_number") or f"crew-{r.get('fire_run__crew__id') or 'n/a'}"
            raw = r.get("total")
            try:
                hours_val = float(raw) if raw is not None else 0.0
            except Exception:
                try:
                    hours_val = float(str(raw))
                except Exception:
                    hours_val = 0.0
            items.append((str(crew_code), hours_val))

        if not items:
            return "-"

        # find primary (match by exact ec_number). Put it first, then others sorted by crew_code
        primary_key = obj.ec_number if getattr(obj, "ec_number", None) is not None else None

        # split into primary and others
        primary_item = None
        others = []
        if primary_key:
            for code, hrs in items:
                if code == primary_key:
                    primary_item = (code, hrs)
                else:
                    others.append((code, hrs))
        else:
            others = items[:]  # no ec_number provided

        # sort others by crew_code
        others.sort(key=lambda x: x[0] or "")

        ordered = []
        if primary_item:
            ordered.append(primary_item)
        ordered.extend(others)

        # allocate estimated hours proportionally across all crews (based on DOF totals)
        sum_hours = sum(h for _, h in items)
        n_crews = len(items)

        rows = []
        for crew_code, crew_hours in ordered:
            if sum_hours > 0:
                est_i = total_est * (crew_hours / sum_hours)
            else:
                est_i = total_est / n_crews if n_crews else 0.0
            diff_i = est_i - crew_hours
            est_s = f"{est_i:.2f}"
            diff_s = f"{diff_i:+.2f}"
            actual_s = f"{crew_hours:.2f}"

            rows.append((crew_code, actual_s, est_s, diff_s))

        list_html = format_html_join(
            "",
            (
                "<li style='margin:2px 0'>"
                "<strong>{}:</strong> DOF=<strong>{}</strong> &nbsp; "
                "Estimated=<strong>{}</strong> &nbsp; diff=<strong>{}</strong></li>"
            ),
            rows,
        )
        return format_html(
            "<ul style='margin:0; padding-left:18px'>{}</ul>",
            list_html
        )

    @admin.display(description="Dispatch")
    def dispatch_title(self, obj):
        url = reverse("admin:dispatch_dispatch_change", args=[obj.pk])
        return format_html('<a href="{}">{}</a>', url, str(obj) or "-")

    @admin.display(
        description="Invoices",
    )
    def invoices_column(self, obj):
        invs = obj.invoices_entries.all()
        if not invs:
            return "-"

        app = Invoice._meta.app_label
        model = Invoice._meta.model_name

        def fmt_amount(x):
            return f"${x:,.2f}" if x is not None else ""

        rows = []
        for inv in invs:
            inv_url = reverse(f"admin:{app}_{model}_change", args=[inv.pk])
            meta_parts = []
            if inv.invoice_amount is not None:
                meta_parts.append(fmt_amount(inv.invoice_amount))
            if inv.status:
                meta_parts.append(inv.status)
            meta_html = " · ".join(meta_parts)

            file_html = ""
            if inv.file:
                filename = os.path.basename(inv.file.name)
                file_html = format_html(
                    '<div style="font-size:12px;">File: <a href="{}" target="_blank" title="{}">{}</a></div>',
                    inv.file.url,
                    inv.file.name,
                    filename,
                )

            rows.append(format_html(
                '<li style="margin:0; padding:6px 0; border-bottom:1px solid #eee;">'
                '<div><a href="{}"><strong>{}</strong></a></div>'
                '<div style="font-size:12px; color:#555;">{}</div>'
                '{}'
                '</li>',
                inv_url,
                inv.invoice_number or f"Invoice #{inv.pk}",
                meta_html,
                file_html,
            ))

        return format_html(
            '<ul style="list-style:none; margin:0; padding:0; line-height:1.35;">{}</ul>',
            format_html_join("", "{}", ((r,) for r in rows)),
        )

    # # CHANGED: optional count column with proper ordering
    # @admin.display(description="# Inv", ordering="_inv_cnt")
    # def invoice_count_col(self, obj):
    #     return obj._inv_cnt
