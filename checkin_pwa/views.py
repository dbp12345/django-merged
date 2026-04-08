from django.apps import apps
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import FieldDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

TARGET_MODEL_SETTING = "CHECKIN_PWA_TARGET_MODEL"
TARGET_FIELD_SETTING = "CHECKIN_PWA_TARGET_FIELD"


def _resolve_checkin_target():
    model_label = getattr(settings, TARGET_MODEL_SETTING, "").strip()
    field_name = getattr(settings, TARGET_FIELD_SETTING, "").strip()

    if not model_label or not field_name:
        return None, None, (
            "Migration mode is active. Saving remains disabled until "
            f"{TARGET_MODEL_SETTING} and {TARGET_FIELD_SETTING} are configured "
            "for a later data-mapping phase."
        )

    try:
        model = apps.get_model(model_label)
    except LookupError:
        return None, None, f"Configured model '{model_label}' could not be resolved."

    try:
        model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return (
            None,
            None,
            f"Configured field '{field_name}' was not found on {model._meta.label}.",
        )

    return model, field_name, ""


@staff_member_required
def checkin_page(request):
    target_model, target_field, integration_status = _resolve_checkin_target()

    return render(
        request,
        "checkin_pwa/checkin.html",
        {
            "integration_enabled": not integration_status,
            "integration_status": integration_status
            or f"Ready to update {target_model._meta.label}.{target_field}.",
            "target_model_label": target_model._meta.label if target_model else "",
            "target_field_name": target_field or "",
        },
    )


@staff_member_required
@require_POST
def scan_checkin(request):
    target_model, target_field, integration_status = _resolve_checkin_target()
    if integration_status:
        return JsonResponse(
            {"success": False, "error": integration_status},
            status=503,
        )

    contact_id = (request.POST.get("contact_id") or "").strip()
    if not contact_id.isdigit():
        return JsonResponse(
            {"success": False, "error": "QR must be a numeric id"},
            status=400,
        )

    try:
        contact = target_model.objects.get(pk=int(contact_id))
    except target_model.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "error": f"{target_model._meta.verbose_name.title()} not found",
            },
            status=404,
        )

    checkin_at = timezone.now()
    setattr(contact, target_field, checkin_at)
    contact.save(update_fields=[target_field])

    return JsonResponse(
        {
            "success": True,
            "id": contact.pk,
            "check_in": checkin_at.isoformat(),
            "model": target_model._meta.label,
            "field": target_field,
        }
    )
