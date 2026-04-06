from django.conf import settings
from django.db import transaction

from paychex.models.PayPeriod import PayPeriod
from core.services.SanitazerService import SanitazerService
from paychex.services.PaychexAPIService import PaychexAPI


def upsert_payperiod_from_item(item: dict) -> PayPeriod:
    """
    Апсёрт одного payperiod-а по item из API.
    Возвращает объект PayPeriod.
    """
    payperiod_id = item.get("payPeriodId")
    if not payperiod_id:
        raise ValueError("Missing payPeriodId in item")

    defaults = {
        "company_id": settings.PAYCHEX_COMPANY_ID,
        "interval_code": item.get("intervalCode"),
        "status": item.get("status"),
        "description": item.get("description"),
        "start_date": SanitazerService.parse_iso_date_to_date(item.get("startDate")),
        "end_date": SanitazerService.parse_iso_date_to_date(item.get("endDate")),
        "submit_by_date": SanitazerService.parse_iso_date_to_date(item.get("submitByDate")),
        "check_date": SanitazerService.parse_iso_date_to_date(item.get("checkDate")),
        "check_count": item.get("checkCount"),
        "raw_json": item,
    }

    with transaction.atomic():
        obj, created = PayPeriod.objects.update_or_create(
            payperiod_id=payperiod_id,
            defaults=defaults
        )
    return obj


def sync_payperiod_from_api(company_id=None, from_date=None, to_date=None):
    api = PaychexAPI()
    api.authenticate()

    total_processed = 0

    resp = api.get_company_pay_periods(company_id=company_id, from_date=from_date, to_date=to_date)

    content = resp.get("content") or []

    payperiods = []
    for item in content:
        obj = upsert_payperiod_from_item(item)
        payperiods.append(obj)
        total_processed += 1
        print(f"Processed {total_processed} PayPeriod...")

    print("Sync finished. Total processed:", total_processed)

    return payperiods
