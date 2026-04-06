from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect

from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from attendance.models import Punch_Event
from attendance.models.PunchEvent import EventType
from company.models import Employees

WAITING_TIME = 10
# WAITING_TIME = 1


class PunchForm(forms.Form):
    note = forms.CharField(max_length=200, required=False)
    # добавь поля, которые реально нужны

@staff_member_required(login_url="pwa_attendance_login")
def punches_form_view(request):
    user = request.user

    employee = Employees.objects.filter(user=user).first()
    # if not employee:
    #     messages.error(request, "Employee не найден для текущего юзера. Проверь связь user→Employees.")
    #     return render(request, "timeclock/punches_form.html", {"employee": None})

    # последний эвент для этого юзера
    last_event = Punch_Event.objects.filter(user=user).order_by("-timestamp").first()

    if request.method == "POST":
        event_type = request.POST.get("event_type")
        valid = {k for k, _ in EventType.choices}
        if event_type not in valid:
            messages.error(request, "Invalid event type")
            return redirect(request.path)

        event_type = (event_type or "").strip()

        now = timezone.now()
        last = Punch_Event.objects.filter(user=user).order_by("-timestamp").first()
        delta = (now - last.timestamp).total_seconds() if last else None

        if last and last.event_type == event_type and delta is not None and delta < WAITING_TIME:
            messages.info(request, "Duplicate ignored")
            return redirect(request.path)

        if last and delta is not None and delta < WAITING_TIME:
            messages.info(request, f"Wait {WAITING_TIME} seconds before retrying.")
            return redirect(request.path)

        try:
            with transaction.atomic():
                last_locked = (
                    Punch_Event.objects.select_for_update()
                    .filter(user=user)
                    .order_by("-timestamp")
                    .first()
                )

                locked_delta = (now - last_locked.timestamp).total_seconds() if last_locked else None
                if last_locked and last_locked.event_type == event_type and locked_delta is not None and locked_delta < WAITING_TIME:
                    messages.info(request, "Duplicate ignored")
                    return redirect(request.path)

                if last_locked and locked_delta is not None and locked_delta < WAITING_TIME:
                    messages.info(request, f"Wait {WAITING_TIME} seconds before retrying.")
                    return redirect(request.path)

                Punch_Event.objects.create(
                    employee=employee,
                    user=user,
                    event_type=event_type,
                    timestamp=now,
                    source="admin",
                )
        except Exception:
            # fallback same rules
            last_fallback = Punch_Event.objects.filter(user=user).order_by("-timestamp").first()
            fallback_delta = (now - last_fallback.timestamp).total_seconds() if last_fallback else None

            if last_fallback and last_fallback.event_type == event_type and fallback_delta is not None and fallback_delta < WAITING_TIME:
                messages.info(request, "Duplicate ignored")
                return redirect(request.path)
            if last_fallback and fallback_delta is not None and fallback_delta < WAITING_TIME:
                messages.info(request, "Quick status change is not supported.")
                return redirect(request.path)

            Punch_Event.objects.create(
                employee=employee,
                user=user,
                event_type=event_type,
                timestamp=now,
                source="admin",
            )

        messages.success(request, "Recorded")
        return redirect(request.path)

    return render(
        request,
        "attendance/punches/punches_form.html",
        {"user": user, "last_event": last_event, "EventType": EventType},
    )
