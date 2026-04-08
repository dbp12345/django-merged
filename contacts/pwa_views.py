from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpRequest
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from .models import Contact


@staff_member_required
@require_GET
def pwa_checkin_page(request: HttpRequest):
    return render(request, "contacts/pwa_checkin.html")


@staff_member_required
@require_POST
def api_checkin_contact(request: HttpRequest, contact_id: int):
    contact = get_object_or_404(Contact, pk=contact_id)

    if not contact.is_active:
        return JsonResponse({"ok": False, "error": "Contact is inactive."}, status=400)

    contact.check_in = timezone.now()
    contact.save(update_fields=["check_in"])

    return JsonResponse(
        {
            "ok": True,
            "contact_id": contact.id,
            "name": str(contact),
            "check_in": contact.check_in.isoformat(),
        }
    )
