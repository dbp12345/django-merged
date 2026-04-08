from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from contacts.models import Contact


@login_required
def scan_qr(request):
    return render(request, "pic_pwa/scan.html")


@login_required
def take_photo(request, contact_id: int):
    contact = get_object_or_404(Contact, pk=contact_id)
    return render(request, "pic_pwa/take_photo.html", {"contact": contact})


@login_required
@require_POST
def upload_photo(request, contact_id: int):
    contact = get_object_or_404(Contact, pk=contact_id)

    f = request.FILES.get("photo")
    if not f:
        return HttpResponseBadRequest("No photo uploaded")

    contact.profile_picture = f
    contact.save(update_fields=["profile_picture"])

    return redirect("pic_take_photo", contact_id=contact.id)
