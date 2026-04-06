from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django_admin_flexlist import FlexListAdmin
from paychex.models import CompanyWorkers, Paycheck
from pdf_plugin.admin_mixin import PDFGenerateMixin


# Inline для чеков на странице CompanyWorkers
class PaycheckInline(admin.TabularInline):
    model = Paycheck
    fk_name = "paychex_worker"
    fields = (
        "check_date",
        "check_type",
        "net",
        "view_link"
    )
    readonly_fields = (
        "check_date",
        "check_type",
        "net",
        "view_link"
    )
    extra = 0
    can_delete = False
    show_change_link = False
    max_num = 0  # запретить добавление из инлайна

    def view_link(self, obj):
        if not obj:
            return "-"
        url = reverse("admin:%s_%s_change" % (obj._meta.app_label, obj._meta.model_name), args=[obj.pk])
        return format_html('<a href="{}" target="_blank">open</a>', url)

    view_link.short_description = "Open"

    # Показываем только последние N чеков — чтобы не тащить тонны строк в форму
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by("-check_date")


@admin.register(CompanyWorkers)
class PaychexCompanyWorkersAdmin(PDFGenerateMixin, FlexListAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_per_page = 500

    autocomplete_fields = (
        "employees",
    )

    # raw_id_fields = (
    #     "employees",
    # )

    inlines = (PaycheckInline,)

    @admin.display(description="worker")
    def worker_str(self, obj):
        string = f"{obj.family_name} {obj.given_name} {obj.middle_name}"
        return string or "-"

    # @admin.display(description="transactions")
    # def transactions_link(self, obj):
    #     # namespace 'paychex' ниже в urls.py — если не хочешь namespace, используй plain path name
    #     url = reverse('paychex_worker_transactions', args=[obj.pk])
    #     return format_html('<a href="{}" target="_blank" rel="noopener">transactions</a>', url)
    #
    # @admin.display(description="transactions")
    # def transactions_panel(self, obj):
    #     url = reverse("paychex_worker_transactions_json", args=[obj.pk])
    #     html = render_to_string("admin/paychex/companyworkers/_transactions_panel.html", {"obj": obj, "url": url})
    #     return format_html(html)

    list_display = (
        "employee_id",
        "worker_str",
        # "family_name",
        # "middle_name",
        # "given_name",
        "employees",
        "worker_id",
        "worker_type",
        "exemption_type",
        "work_state",
        "birth_date",
        "sex",
        "hire_date",
        "legal_id_type",
        "legal_id_value",
        # "labor_assignment_id",
        # "location_id",
        # "organization_id",
        "organization_name",
        "organization_number",
        # "worker_status_id",
        "status_type",
        "status_reason",
        "status_effective_date",
    )

    fields = (
        "employee_id",
        "worker_str",
        # ("family_name", "middle_name", "given_name",),
        "employees",
        "worker_id",
        "worker_type",
        "exemption_type",
        "work_state",
        "birth_date",
        "sex",
        "hire_date",
        "legal_id_type",
        "legal_id_value",
        # "labor_assignment_id",
        # "location_id",
        # "organization_id",
        "organization_name",
        "organization_number",
        # "worker_status_id",
        "status_type",
        "status_reason",
        "status_effective_date",
        # "transactions_link",
        # "transactions_panel",
    )

    readonly_fields = (
        "family_name",
        "middle_name",
        "given_name",
        "worker_str",
        "worker_id",
        "employee_id",
        "worker_type",
        "exemption_type",
        "work_state",
        "birth_date",
        "sex",
        "hire_date",
        "legal_id_type",
        "legal_id_value",
        # "labor_assignment_id",
        # "location_id",
        # "organization_id",
        "organization_name",
        "organization_number",
        # "worker_status_id",
        "status_type",
        "status_reason",
        "status_effective_date",
        # "transactions_link",
        # "transactions_panel",
    )

    search_fields = (
        "employees__email",
        "given_name",
        "middle_name",
        "family_name",
        "worker_id",
        "employee_id",
        "legal_id_value"
    )
    list_filter = (
        "worker_type",
        "exemption_type",
        "status_type",
        "sex",
        "legal_id_type",
        "organization_name",
        "work_state",
        "status_reason"
    )

    ordering = ("status_effective_date",)

    # class Media:
    # js = ("paychex/js/transactions_panel.js",)
    # css = {"all": ("paychex/css/transactions_panel.css",)}
