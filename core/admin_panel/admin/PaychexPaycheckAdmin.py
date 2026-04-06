from django.contrib import admin
from paychex.models import Paycheck, PaycheckComponent
from pdf_plugin.admin_mixin import PDFGenerateMixin


# Inline для компонентов (на странице Paycheck)
class PaycheckComponentInline(admin.TabularInline):
    model = PaycheckComponent
    fk_name = "paycheck"
    fields = (
        "name",
        "component_type",
        "classification_type",
        "amount",
        "rate",
        "hours",
        "organization_name",
    )
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = False
    verbose_name = "Component"
    verbose_name_plural = "Components"


# Админ для Paycheck — чтобы можно было открыть чек и увидеть компоненты
@admin.register(Paycheck)
class PaychexPaycheckAdmin(PDFGenerateMixin, admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    autocomplete_fields = (
        "paychex_worker",
    )

    # raw_id_fields = (
    #     "paychex_worker",
    # )

    list_per_page = 500

    list_display = (
        "paychex_worker",
        "check_type",
        "check_date",
        "check_number",
        "net",
    )
    fields = (
        "paychex_worker",
        "check_type",
        "check_date",
        "check_number",
        "net",
    )
    search_fields = (
        "paycheck_id",
        "worker_id",
        "check_number",
        "paychex_worker__family_name",
        "paychex_worker__given_name",
        "paychex_worker__legal_id_value",
    )
    list_filter = (
        "paychex_worker",
        "check_type",
    )
    readonly_fields = (
        "paychex_worker",
        "check_type",
        "check_date",
        "check_number",
        "net",
    )
    inlines = (PaycheckComponentInline,)
    ordering = ("-check_date",)
