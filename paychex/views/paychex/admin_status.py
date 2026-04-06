from itertools import groupby
from datetime import datetime, timedelta
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
from django.shortcuts import render

from paychex.models import TimePunch
from paychex.services.punch_upsert import upsert_timepunch_rows_and_sync, get_admins_companyworker_employee_ids


def _fmt_time(val, tz):
    """Возвращает 'HH:MM' или '' — безопасно для None/str/naive/aware."""
    if not val:
        return "None"
    if isinstance(val, str):
        # если вдруг уже строка — дай как есть (обычно не так, но безопасно)
        return val
    try:
        # если naive — предположим локальную зону и поставить tzinfo
        if val.tzinfo is None:
            val = val.replace(tzinfo=tz)
        return val.astimezone(tz).strftime("%H:%M")
    except Exception:
        return str(val)


def employees_status_view(request):
    timedelta_days = int(request.GET.get("delta", "0"))

    ids = get_admins_companyworker_employee_ids()  # [2171, 2175]
    # синхронизируем панчи (делает upsert в бд)
    res = upsert_timepunch_rows_and_sync(ids, sync=True, timedelta_days=timedelta_days)

    tz = ZoneInfo("America/Los_Angeles")
    # всегда работаем с date()
    if timedelta_days != 0:
        today = (datetime.now(tz) + timedelta(days=timedelta_days)).date()
    else:
        today = datetime.now(tz).date()

    punches = list(
        TimePunch.objects
        .filter(apply_to_date=today)
        .order_by("emp_identifier", "in_time")
        .values(
            "emp_identifier", "first_name", "last_name",
            "in_time", "out_time", "in_time_slice_preid", "out_time_slice_preid"
        )
    )

    rows = []
    for emp_id, group in groupby(punches, key=lambda x: x["emp_identifier"]):
        items = list(group)
        latest = items[-1]
        is_online = (latest["out_time"] is None)
        punches_short = [
            {"in": _fmt_time(x["in_time"], tz), "out": _fmt_time(x["out_time"], tz)}
            for x in items
        ]

        rows.append({
            "emp_identifier": emp_id,
            "name": f"{latest.get('first_name') or ''} {latest.get('last_name') or ''}".strip(),
            "is_online": is_online,
            "punches": punches_short,
        })

    rows.sort(key=lambda r: r["name"] or r["emp_identifier"])
    title = f'Employees time status {today.strftime("%m/%d/%Y")}'

    # build navigation URLs preserving other GET params but replacing delta
    def _build_url(new_delta: int) -> str:
        q = dict(request.GET.items())
        q["delta"] = str(new_delta)
        return f"{request.path}?{urlencode(q)}"

    prev_url = _build_url(timedelta_days - 1)
    # If delta >= 0 then there is no future data -> hide next arrow
    # English comment: avoid exposing "next" when no future data exists
    next_url = _build_url(timedelta_days + 1) if timedelta_days < 0 else None
    today_url = _build_url(0)

    return render(
        request,
        "admin/paychex/employees_status.html",
        {
            "title": title,
            "rows": rows,
            "delta": timedelta_days,
            "prev_url": prev_url,
            "next_url": next_url,
            "today_url": today_url,
            "display_date": today.strftime("%m/%d/%Y")
        },
    )
