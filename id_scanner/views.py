from __future__ import annotations

import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from contacts.models import Contact

from .models import IDScanGroup, IDScanRecord, IDScanTemplate
from .services import ScanDependencyError, ScanProcessingError, process_record

logger = logging.getLogger(__name__)


@login_required(login_url="/admin/login/")
def dashboard(request):
    groups = list(
        IDScanGroup.objects.filter(is_active=True)
        .prefetch_related("templates__fields")
        .order_by("name")
    )
    recent_records = IDScanRecord.objects.select_related("template", "contact").all()[:10]
    group_payload = [
        {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "steps": group.enabled_steps,
            "templates": [
                {
                    "id": template.id,
                    "name": template.name,
                    "group_id": group.id,
                    "document_type": template.get_document_type_display(),
                    "issuer_region": template.issuer_region,
                }
                for template in group.templates.filter(is_active=True).order_by("name")
            ],
        }
        for group in groups
    ]
    return render(
        request,
        "id_scanner/dashboard.html",
        {
            "groups": groups,
            "recent_records": recent_records,
            "group_payload": group_payload,
        },
    )


@login_required(login_url="/admin/login/")
@require_http_methods(["POST"])
def scan_submit(request):
    image_file = request.FILES.get("image")
    group_id = (request.POST.get("group_id") or "").strip()
    template_id = (request.POST.get("template_id") or "").strip()
    contact_id = (request.POST.get("contact_id") or "").strip()

    if not image_file:
        return JsonResponse({"success": False, "error": "Upload an image first."}, status=400)
    if not group_id.isdigit() or not template_id.isdigit():
        return JsonResponse({"success": False, "error": "Choose a scan group and template."}, status=400)

    try:
        group = IDScanGroup.objects.get(pk=int(group_id), is_active=True)
        template = IDScanTemplate.objects.get(pk=int(template_id), group=group, is_active=True)
    except (IDScanGroup.DoesNotExist, IDScanTemplate.DoesNotExist):
        return JsonResponse({"success": False, "error": "The selected group or template is not available."}, status=404)

    contact = None
    if contact_id:
        if not contact_id.isdigit():
            return JsonResponse({"success": False, "error": "Contact ID must be numeric."}, status=400)
        try:
            contact = Contact.objects.get(pk=int(contact_id))
        except Contact.DoesNotExist:
            return JsonResponse({"success": False, "error": "Contact not found."}, status=404)

    record = IDScanRecord.objects.create(
        group=group,
        template=template,
        contact=contact,
        source_image=image_file,
    )

    try:
        process_record(record)
    except ScanDependencyError as exc:
        record.status = IDScanRecord.STATUS_ERROR
        record.error_message = str(exc)
        record.save(update_fields=["status", "error_message", "updated_at"])
        return JsonResponse({"success": False, "error": str(exc), "record_id": record.pk}, status=503)
    except ScanProcessingError as exc:
        record.status = IDScanRecord.STATUS_ERROR
        record.error_message = str(exc)
        record.save(update_fields=["status", "error_message", "updated_at"])
        return JsonResponse({"success": False, "error": str(exc), "record_id": record.pk}, status=422)
    except Exception as exc:
        logger.exception("Unexpected scanner failure for record %s", record.pk)
        raw_message = str(exc).strip()
        error_message = f"{exc.__class__.__name__}: {raw_message}" if raw_message else exc.__class__.__name__
        record.status = IDScanRecord.STATUS_ERROR
        record.error_message = error_message
        record.save(update_fields=["status", "error_message", "updated_at"])
        return JsonResponse(
            {"success": False, "error": error_message, "record_id": record.pk},
            status=500,
        )

    return JsonResponse(
        {
            "success": True,
            "record_id": record.pk,
            "status": record.status,
            "confidence_score": float(record.confidence_score or 0),
            "fields": record.extracted_data,
            "artifacts": {
                "source": record.source_image.url if record.source_image else "",
                "warped": record.warped_image.url if record.warped_image else "",
                "processed": record.processed_image.url if record.processed_image else "",
            },
        }
    )
