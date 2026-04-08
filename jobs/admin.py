from django.contrib import admin
from .models import Job
from pdf_plugin.admin_mixin import PDFGenerateMixin 

@admin.register(Job)
class JobAdmin(PDFGenerateMixin,admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'company',
        'customer',
        'status',
        'start_date',
        'end_date',
    )
    list_filter = ('company', 'status')
    search_fields = ('title', 'description')
