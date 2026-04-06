import hashlib
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from attendance.models.PunchEvent import EventType
from exchange.models import Contacts_Prop
from paychex.models import TimePunch, CompanyWorkers
from paychex.services.FlexTimeClientService import FlexTimeTWS
from synchronization.services.SyncDeliveryService import SyncDeliveryService


def _calc_row_hash(row: dict) -> str:
    s = json.dumps(row, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def _make_external_id(row: dict) -> str:
    in_sid = int(row.get("InTimeSlicePreID") or 0)
    out_sid = int(row.get("OutTimeSlicePreID") or 0)
    if in_sid > 0:
        return f"in-{in_sid}"
    if out_sid > 0:
        return f"out-{out_sid}"
    # fallback: короткий хеш по временам + emp
    s = f"{row.get('EmpIdentifier') or ''}|{row.get('InTime') or ''}|{row.get('OutTime') or ''}"
    return "h-" + hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]


def _parse_dt(ts: str, tz: ZoneInfo):
    if not ts:
        return None
    for fmt in ("%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M"):
        try:
            dt = datetime.strptime(ts, fmt)
            return dt.replace(tzinfo=tz)
        except Exception:
            continue
    return None


def upsert_timepunch_rows(rows: list, tz: ZoneInfo):
    created = 0
    updated = 0

    for r in rows:
        emp = str(r.get("EmpIdentifier") or "")
        ext = _make_external_id(r)
        row_hash = _calc_row_hash(r)

        defaults = {
            "raw": r,
            "first_name": r.get("FirstName"),
            "last_name": r.get("LastName"),
            "apply_to_date": None,
            "in_time": _parse_dt(r.get("InTime") or r.get("InTimeActual"), tz),
            "in_time_actual": _parse_dt(r.get("InTimeActual") or r.get("InTime"), tz),
            "out_time": _parse_dt(r.get("OutTime") or r.get("OutTimeActual"), tz),
            "in_time_slice_preid": int(r.get("InTimeSlicePreID") or 0) or None,
            "out_time_slice_preid": int(r.get("OutTimeSlicePreID") or 0) or None,
            "in_latitude": (
                float(r.get("InLatitude"))
                if r.get("InLatitude") not in (None, "")
                else None
            ),
            "in_longitude": (
                float(r.get("InLongitude"))
                if r.get("InLongitude") not in (None, "")
                else None
            ),
            "out_latitude": (
                float(r.get("OutLatitude"))
                if r.get("OutLatitude") not in (None, "")
                else None
            ),
            "out_longitude": (
                float(r.get("OutLongitude"))
                if r.get("OutLongitude") not in (None, "")
                else None
            ),
            "in_type": r.get("InType"),
            "out_type": r.get("OutType"),
            "pay_type_id": (
                int(r.get("PayTypeID"))
                if r.get("PayTypeID") not in (None, "")
                else None
            ),
            "pay_type_name": r.get("PayTypeName"),
            "pay_type_code": r.get("PayTypeCode"),
            "regular_minutes": int(r.get("RegularMinutes") or 0) or None,
            "unpaid_minutes": int(r.get("UnpaidMinutes") or 0) or None,
            "ot_info": r.get("OTInfo") or [],
            "labor_levels": {},  # optional, populate if нужно
            "in_clock_id": r.get("InClockID") or None,
            "out_clock_id": r.get("OutClockID") or None,
            "export_code": r.get("ExportCode"),
            "row_hash": row_hash,
            "external_id": ext,
        }

        # apply_to_date parsing
        atd = r.get("ApplyToDate")
        if atd:
            try:
                defaults["apply_to_date"] = datetime.strptime(atd, "%m/%d/%Y").date()
            except Exception:
                defaults["apply_to_date"] = None

        # минимал: используем update_or_create по уникальной паре
        try:
            obj, created_flag = TimePunch.objects.update_or_create(
                emp_identifier=emp,
                external_id=ext,
                defaults=defaults,
            )
        except IntegrityError:
            # редкий случай гонки: пробуем создать заново с транзакцией
            try:
                with transaction.atomic():
                    obj, created_flag = TimePunch.objects.update_or_create(
                        emp_identifier=emp,
                        external_id=ext,
                        defaults=defaults,
                    )
            except Exception:
                raise  # пусть наружу выходит — ты просил минимально ловить ошибки

        if created_flag:
            created += 1
        else:
            updated += 1

    return created, updated


def upsert_timepunch_rows_and_sync(ids: list, sync: bool, timedelta_days=0):
    tz = ZoneInfo("America/Los_Angeles")
    svc = FlexTimeTWS()
    if timedelta_days != 0:
        resp = svc.get_punches_for_local_day(
            ids, datetime.now(tz) + timedelta(days=timedelta_days)
        )
    else:
        resp = svc.get_punches_for_local_day(ids, datetime.now(tz))
    rows = svc._extract_rows(resp)

    if sync:
        status_map = simple_enrich_rows(rows, tz)
        for emp_id, info in status_map.items():
            employees = info["employees"]
            is_online = info["is_online"]

            if is_online:
                value = EventType.CLOCK_IN
            else:
                value = EventType.CLOCK_OUT

            if employees:
                property_name = "Employee Working Status"
                contacts_prop_instance = Contacts_Prop.objects.get(
                    property_name=property_name
                )
                SyncDeliveryService.do_sync_parameters(
                    employees,
                    contacts_prop_instance,
                    value=value,
                    modified_by="upsert_timepunch_rows",
                    privser=True,
                    exchange=False,
                )

    return upsert_timepunch_rows(rows, tz)


def simple_enrich_rows(rows: list, tz):
    result = {}
    today = datetime.now(tz).date()

    for r in rows:
        emp_id = str(r.get("EmpIdentifier") or "")
        # получаем CompanyWorkers (каждый вызов — запрос)
        cw = CompanyWorkers.objects.filter(employee_id=emp_id).first()
        # пытаемся получить Employees: сначала через cw.employee (если FK есть), иначе по contact_id, иначе по pk
        emp = None
        if cw is not None:
            emp = getattr(cw, "employees", None)
        # if emp is None:
        #     emp = код по поиску Employees

        # простой is_online: ApplyToDate == today и OutTime пустой
        is_online = False
        atd = (r.get("ApplyToDate") or "").strip()  # "MM/DD/YYYY"
        out_time = (r.get("OutTime") or "").strip()
        try:
            if atd:
                mm, dd, yyyy = atd.split("/")
                dt = datetime(int(yyyy), int(mm), int(dd)).date()
                if dt == today and out_time == "":
                    is_online = True
        except Exception:
            # молчим — minimal code как просил
            is_online = False

        result[emp_id] = {
            "companyworker": cw,
            "employees": emp,
            "is_online": is_online,
            "row": r,
        }

    return result


# для получения списка юзерв, к которым применяется получение панчей.
# Место не подходящее, но как обычно надо "очень быстро и на вчера"
def get_admins_companyworker_employee_ids():
    admins = list(
        get_user_model()
        .objects.filter(is_active=True, is_staff=True)
        .values("id", "email", "username")
    )
    if not admins:
        return {}

    id_to = {a["id"]: a["username"] for a in admins}
    admin_ids = list(id_to.keys())

    cw_rows = (
        CompanyWorkers.objects.filter(employees__user__id__in=admin_ids)
        .select_related("employees__user")
        .values_list("employees__user__id", "employee_id")
    )

    result = []
    for user_id, employee_id in cw_rows:
        result.append(employee_id)
    #
    # result = {email: [] for email in id_to.values()}
    # for user_id, employee_id in cw_rows:
    #     result[id_to[user_id]].append(employee_id)

    return result
