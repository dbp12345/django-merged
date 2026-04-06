from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin
from core.models import  Documentation_Page

@admin.register(Documentation_Page)
class DocumentationPageAdmin(MarkdownxModelAdmin):
    list_display = ("title", "slug")
    search_fields = ("title", "slug")
    # list_editable = ("slug",)