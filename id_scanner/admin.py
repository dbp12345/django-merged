from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import IDScanField, IDScanGroup, IDScanRecord, IDScanTemplate


class IDScanFieldInline(admin.TabularInline):
    model = IDScanField
    extra = 1
    fields = (
        "order",
        "key",
        "label",
        "field_type",
        "roi_left",
        "roi_top",
        "roi_width",
        "roi_height",
        "psm",
        "whitelist",
        "validation_regex",
        "expected_length",
        "required",
    )


@admin.register(IDScanGroup)
class IDScanGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "threshold_mode", "default_psm")
    list_filter = ("is_active", "threshold_mode")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {"fields": ("name", "slug", "description", "is_active")}),
        (
            "Pipeline",
            {
                "fields": (
                    "grayscale_enabled",
                    "upscale_enabled",
                    "deskew_enabled",
                    "binarize_enabled",
                    "noise_removal_enabled",
                    "isolate_roi_enabled",
                    "optimize_ocr_enabled",
                    "apply_psm_enabled",
                    "apply_whitelist_enabled",
                    "post_process_enabled",
                    "data_validation_enabled",
                    "remove_background_enabled",
                    "level_perspective_enabled",
                )
            },
        ),
        (
            "OCR Defaults",
            {
                "fields": (
                    "scale_factor",
                    "default_psm",
                    "default_whitelist",
                    "threshold_mode",
                )
            },
        ),
    )


@admin.register(IDScanTemplate)
class IDScanTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "document_type", "issuer_region", "is_active", "roi_preview_button")
    list_filter = ("group", "document_type", "is_active")
    search_fields = ("name", "slug", "issuer_region", "notes")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("roi_preview_link",)
    fields = (
        "group",
        "name",
        "slug",
        "document_type",
        "issuer_region",
        "notes",
        "is_active",
        "target_width",
        "target_height",
        "accepted_date_input_formats",
        "roi_preview_link",
    )
    inlines = [IDScanFieldInline]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:template_id>/roi-preview/",
                self.admin_site.admin_view(self.roi_preview_view),
                name="id_scanner_idscantemplate_roi_preview",
            ),
        ]
        return custom_urls + urls

    def roi_preview_button(self, obj: IDScanTemplate):
        url = reverse("admin:id_scanner_idscantemplate_roi_preview", args=[obj.pk])
        return format_html('<a class="button" href="{}">ROI Preview</a>', url)

    roi_preview_button.short_description = "ROI Preview"

    def roi_preview_link(self, obj: IDScanTemplate):
        if not obj.pk:
            return "Save this template first to open ROI Preview."
        url = reverse("admin:id_scanner_idscantemplate_roi_preview", args=[obj.pk])
        return format_html('<a href="{}">Open ROI Preview</a>', url)

    roi_preview_link.short_description = "ROI Preview"

    def roi_preview_view(self, request, template_id: int):
        template = get_object_or_404(IDScanTemplate.objects.select_related("group"), pk=template_id)
        fields = list(template.fields.order_by("order", "id"))
        field_payload = [
            {
                "key": field.key,
                "label": field.label,
                "field_type": field.get_field_type_display(),
                "required": field.required,
                "roi_left": float(field.roi_left),
                "roi_top": float(field.roi_top),
                "roi_width": float(field.roi_width),
                "roi_height": float(field.roi_height),
                "psm": field.psm or template.group.default_psm,
                "whitelist": field.whitelist or template.group.default_whitelist,
                "validation_regex": field.validation_regex,
                "expected_length": field.expected_length,
            }
            for field in fields
        ]
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": template,
            "title": f"ROI Preview: {template.name}",
            "template_obj": template,
            "fields": fields,
            "field_payload": field_payload,
            "change_url": reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                args=[template.pk],
            ),
        }
        return TemplateResponse(
            request,
            "admin/id_scanner/idscantemplate/roi_preview.html",
            context,
        )


@admin.register(IDScanRecord)
class IDScanRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "status",
        "template",
        "contact",
        "confidence_score",
    )
    list_filter = ("status", "group", "template")
    search_fields = ("id", "contact__first_name", "contact__last_name", "error_message")
    readonly_fields = (
        "created_at",
        "updated_at",
        "processed_at",
        "raw_ocr_text",
        "extracted_data",
    )
