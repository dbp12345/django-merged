from dalf.admin import DALFRelatedFieldAjax, DALFModelAdmin
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.utils.html import format_html
from django_admin_flexlist import FlexListAdmin
from dispatch.models import Invoice
from decimal import Decimal
from django.db.models import Sum
from django.template.response import TemplateResponse
from dispatch.models.Invoice import Status
from pdf_plugin.admin_mixin import PDFGenerateMixin

PAID_STATUSES = (Status.PAID,)


@admin.register(Invoice)
class InvoiceAdmin(PDFGenerateMixin, FlexListAdmin, DALFModelAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 100
    search_fields = (
        "invoice_number",
        "dispatch__fire__incident_name",
        "dispatch__fire__fire_number",
        "dispatch__ec_number",
        "invoice_amount",
        "check_amount",
        # "dispatch__company",
    )
    autocomplete_fields = ("dispatch",)
    list_display_links = ("updated_at",)
    list_display = (
        "updated_at",
        "dispatch",
        "invoice_date",
        "status",
        "dispatch__company",
        "invoice_number",
        "dispatch__fire__incident_name",
        "dispatch__fire__fire_number",
        "dispatch__ec_number",
        "start_date",
        "finish_date",
        "number_of_days",
        "invoice_amount",
        "dispatch__crew__crew_boss",
        "date_paid",
        "check_amount",
        "change_in_payment_calculation",
        "file",
        "notes",
    )
    list_editable = (
        "dispatch",
        "invoice_date",
        "status",
        "invoice_number",
        "start_date",
        "finish_date",
        "number_of_days",
        "invoice_amount",
        "date_paid",
        "check_amount",
        # "change_in_payment",
    )
    ordering = ("-updated_at",)
    fields = (
        "dispatch",
        "invoice_date",
        "status",
        "invoice_number",
        "start_date",
        "finish_date",
        "number_of_days",
        "invoice_amount",
        "date_paid",
        "check_amount",
        "change_in_payment_calculation",
        "file",
        "notes",
        ("created_at", "updated_at")
    )
    readonly_fields = (
        "change_in_payment_calculation",
        "created_at",
        "updated_at",
    )
    list_filter = (
        ("dispatch", DALFRelatedFieldAjax),
        "invoice_date",
        "status",
        "dispatch__company",
        "dispatch__ec_number",
        "start_date",
        "finish_date",
        "date_paid",
    )

    class Media:
        css = {
            "all": (
                "core/DALFRelatedFieldAjax.css",
                # "grappelli/css/admin_breadcrumbs.css",
            )
        }

    @admin.display(description="Change in Payment")
    def change_in_payment_calculation(self, obj):
        # если каких-то сумм нет — ничего считать не будем
        if obj.invoice_amount is None or obj.check_amount is None:
            return "0.00"
        try:
            change = obj.check_amount - obj.invoice_amount
        except Exception:
            return "0.00"
        text = f"{change:,.2f}"
        if change > 0:
            return format_html('<span style="color: green;">{}</span>', text)
        elif change < 0:
            return format_html('<span style="color: red;">{}</span>', text)
        else:
            return text

    # def changelist_view(self, request, extra_context=None):
    #     response = super().changelist_view(request, extra_context=extra_context)
    #
    #     # (не обязательно) жёстко укажем путь к шаблону для этой модели
    #     if isinstance(response, TemplateResponse):
    #         # Определим, какой шаблон реально собираются рендерить
    #         names = []
    #         if getattr(response, "template_name_list", None):
    #             names = list(response.template_name_list)
    #         elif getattr(response, "template_name", None):
    #             t = response.template_name
    #             names = [t] if isinstance(t, str) else list(t)
    #
    #         if any("change_list" in str(n) for n in names):
    #             response.template_name = "admin/dispatch/invoice/change_list.html"
    #             if getattr(response, "template_name_list", None):
    #                 response.template_name_list = ["admin/dispatch/invoice/change_list.html"]
    #
    #     # прокидываем суммы в контекст текущего queryset (учтёт фильтры/поиск)
    #     if hasattr(response, "context_data") and response.context_data and "cl" in response.context_data:
    #         qs = response.context_data["cl"].queryset
    #         paid_total = qs.filter(status__in=PAID_STATUSES).aggregate(s=Sum("invoice_amount"))["s"] or Decimal("0")
    #         not_paid_total = qs
    # .exclude(status__in=PAID_STATUSES)
    # .aggregate(s=Sum("invoice_amount"))["s"] or Decimal("0")
    #         response.context_data["summary_paid_total"] = paid_total
    #         response.context_data["summary_not_paid_total"] = not_paid_total
    #
    #     return response

    def changelist_view(self, request, extra_context=None):
        resp = super().changelist_view(request, extra_context=extra_context)

        # Подменяем шаблон только для changelist
        if isinstance(resp, TemplateResponse):
            ctx = getattr(resp, "context_data", None) or {}
            cl = ctx.get("cl")
            if isinstance(cl, ChangeList):
                resp.template_name = "admin/dispatch/invoice/change_list.html"
                if getattr(resp, "template_name_list", None) is not None:
                    resp.template_name_list = ["admin/dispatch/invoice/change_list.html"]

                # здесь же можно класть твои суммы, раз уже знаем что это changelist
                qs = cl.queryset
                paid_total = qs.filter(status__in=PAID_STATUSES).aggregate(
                    s=Sum("invoice_amount")
                )["s"] or Decimal("0")
                not_paid_total = qs.exclude(status__in=PAID_STATUSES).aggregate(
                    s=Sum("invoice_amount")
                )["s"] or Decimal("0")
                resp.context_data["summary_paid_total"] = f"{paid_total:,.2f}"
                resp.context_data["summary_not_paid_total"] = f"{not_paid_total:,.2f}"

        return resp
