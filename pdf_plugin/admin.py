from django.contrib import admin

from .models import PDFFieldMap, PDFRenderLog, PDFTemplate


@admin.register(PDFTemplate)
class PDFTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "version", "enabled", "root_model_label", "created_at")
    list_filter = ("enabled", "root_model_label")
    search_fields = ("name", "root_model_label")
    readonly_fields = ("created_at", "updated_at")
    # Hide flatten field - proper implementation requires explicit appearance stream generation
    # which is complex in pypdf. Always use flatten=False.
    exclude = ("flatten",)
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": ("name", "version", "enabled", "root_model_label"),
            },
        ),
        (
            "PDF File",
            {
                "fields": ("template_file",),
            },
        ),
        (
            "Output Settings",
            {
                "fields": ("output_filename_pattern",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(PDFFieldMap)
class PDFFieldMapAdmin(admin.ModelAdmin):
    list_display = ("template", "pdf_field_name", "value_path", "default_value", "enabled", "order")
    list_filter = ("template", "enabled")
    search_fields = ("pdf_field_name", "value_path", "default_value")
    ordering = ("template", "order", "pdf_field_name")


@admin.register(PDFRenderLog)
class PDFRenderLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "template_name",
        "template_version",
        "root_model_label",
        "root_pk",
        "user",
        "success",
    )
    list_filter = ("success", "template_name", "root_model_label", "created_at")
    search_fields = (
        "root_pk",
        "template_name",
        "error_message",
        "user__username",
        "user__email",
    )
    readonly_fields = [f.name for f in PDFRenderLog._meta.fields]
    date_hierarchy = "created_at"
