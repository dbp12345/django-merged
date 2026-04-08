from django.contrib import admin
from .models import Invoice
from pdf_plugin.admin_mixin import PDFGenerateMixin 


@admin.register(Invoice)
class InvoiceAdmin(PDFGenerateMixin,admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "company",
        "job",
        "status",
        "issue_date",
        "due_date",
        "total",
    )
    list_filter = ("status",)   # MUST be tuple or list
    search_fields = ("invoice_number",)
