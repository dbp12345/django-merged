from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404

from .models import PDFTemplate
from .services import render_pdf_for_instance


@staff_member_required
def render_pdf_admin(request: HttpRequest, template_name: str, pk: str):
    tpl = get_object_or_404(PDFTemplate, name=template_name, enabled=True)

    app_label, model_name = tpl.root_model_label.split(".", 1)
    from django.apps import apps

    model = apps.get_model(app_label, model_name)
    obj = get_object_or_404(model, pk=pk)

    perm_codename = f"{app_label}.view_{model._meta.model_name}"
    if not request.user.has_perm(perm_codename):
        return HttpResponseForbidden("Missing permission.")

    result = render_pdf_for_instance(
        tpl,
        obj,
        user=request.user,
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )

    resp = HttpResponse(result.pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{result.filename}"'
    return resp
