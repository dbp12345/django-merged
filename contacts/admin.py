from django.contrib import admin
from django.utils.html import format_html

from .models import Contact
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(Contact)
class ContactAdmin(PDFGenerateMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "role",
        "company",
        "email",
        "phone",
        "is_active",
        "profile_picture_thumb",
    )

    list_filter = ("role", "company", "is_active")
    search_fields = ("first_name", "last_name", "email")

    readonly_fields = ("profile_picture_thumb",)

    # ---------- helpers ----------

    def full_name(self, obj: Contact):
        return f"{obj.first_name} {obj.last_name}".strip()

    full_name.short_description = "Name"

    def profile_picture_thumb(self, obj: Contact):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="height:80px;width:auto;border-radius:8px;" />',
                obj.profile_picture.url,
            )
        return "(no photo)"

    profile_picture_thumb.short_description = "Profile picture"
