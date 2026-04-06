from django.contrib import admin
from django_admin_flexlist import FlexListAdmin

from company.models.BankTransaction import BankTransaction
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(BankTransaction)
class BankTransactionAdmin(PDFGenerateMixin, FlexListAdmin):
    list_per_page = 100
    search_fields = (
        "bank_number",
        "account_number",
        "description",
        "type",
        "category",
        "project_code",
        "user__username",
        "user__email",
    )
    autocomplete_fields = ("user",)
    list_display_links = ("updated_at",)

    list_display = (
        "updated_at",
        # "date",
        # "time",
        "datetime",
        "bank_name",
        "bank_number",
        "account_number",
        "amount",
        "user",
        "description",
        "type",
        "category",
        "project_code",
        "fixed_variable",
        "required_discretionary",
        "approved",
        "growth",
        # "file",
        "file_preview",
    )

    list_editable = (
        # "date",
        # "time",
        # "datetime",
        # "bank_name",
        # "bank_number",
        # "account_number",
        # "amount",
        # "description",
        # "type",
        # "category",
        # "project_code",
        # "fixed_variable",
        # "required_discretionary",
        # "approved",
        # "growth",
        # "file",
    )

    ordering = ("-datetime", "-updated_at")

    fields = (
        # "date",
        # "time",
        "datetime",
        "bank_name",
        "bank_number",
        "account_number",
        "amount",
        "user",
        "description",
        "type",
        "category",
        "project_code",
        "fixed_variable",
        "required_discretionary",
        "approved",
        "growth",
        "file",
        "file_preview",
        ("created_at", "updated_at"),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "file_preview",
    )

    list_filter = (
        "bank_name",
        # "date",
        "datetime",
        "user",
        "type",
        "category",
        "project_code",
        "fixed_variable",
        "required_discretionary",
        "approved",
        "growth",
    )
