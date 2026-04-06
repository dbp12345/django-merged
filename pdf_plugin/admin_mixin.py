from __future__ import annotations

from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import PDFTemplate


class PDFGenerateMixin(admin.ModelAdmin):
    """
    Add a "Generate PDF" section on the change page listing templates
    configured for this model.
    """

    change_form_template = "pdf_plugin/change_form_with_pdf.html"

    def get_pdf_templates_for_obj(self, obj):
        label = f"{obj._meta.app_label}.{obj.__class__.__name__}"
        return PDFTemplate.objects.filter(enabled=True, root_model_label=label).order_by(
            "name", "version"
        )

    def render_pdf_links_html(self, obj):
        templates = self.get_pdf_templates_for_obj(obj)
        if not templates.exists():
            return mark_safe("<em>No PDF templates configured for this model.</em>")

        items = []
        for t in templates:
            url = reverse("pdf_plugin_render_admin", args=[t.name, str(obj.pk)])
            items.append(
                f'<li><a href="{url}">{t.name} (v{t.version})</a></li>'
            )

        return mark_safe(
            "<ul style='margin:0;padding-left:18px;'>" + "".join(items) + "</ul>"
        )

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["pdf_plugin_enabled"] = True
        extra_context["pdf_plugin_links_html"] = ""
        if object_id:
            obj = self.get_object(request, object_id)
            if obj:
                extra_context["pdf_plugin_links_html"] = self.render_pdf_links_html(obj)
        return super().changeform_view(request, object_id, form_url, extra_context)
