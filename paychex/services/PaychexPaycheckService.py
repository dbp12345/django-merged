from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.conf import settings

from paychex.models import Paycheck, PaycheckComponent
from paychex.services.PaychexAPIService import PaychexAPI
from paychex.models.CompanyWorkers import CompanyWorkers
from core.services.SanitazerService import SanitazerService

def _to_decimal_safe(v):
    if v is None:
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, TypeError, ValueError):
        return None

def _parse_date(s):
    return SanitazerService.parse_iso_date_to_date(s)

def upsert_paycheck_from_item(item: dict, company_id: str = None) -> Paycheck:
    """
    Минимальный апсёрт чека: сохраняем основные поля и raw_json.
    Компоненты сохраняем как есть (earnings/deductions/taxes).
    """
    paycheck_id = item.get("paycheckId") or item.get("id") or item.get("checkId")
    if not paycheck_id:
        raise ValueError("No paycheck id in item")

    worker_id = item.get("workerId")
    paychex_worker = CompanyWorkers.objects.filter(worker_id=worker_id).first() if worker_id else None

    defaults = {
        "company_id": company_id or getattr(settings, "PAYCHEX_COMPANY_ID", None),
        "payperiod_id": item.get("payPeriodId") or item.get("payperiodId"),
        "worker_id": worker_id,
        "paychex_worker": paychex_worker,
        "check_date": _parse_date(item.get("checkDate") or item.get("payDate")),
        # сохраняем net прямо как пришло
        "net": _to_decimal_safe(item.get("netPay") or item.get("netAmount") or item.get("net")),
        # не вычисляем gross, пусть остаётся NULL если API не дал
        "gross": _to_decimal_safe(item.get("grossAmount") or item.get("gross")) if (item.get("grossAmount") or item.get("gross")) is not None else None,
        "raw_json": item,
    }

    # дополнительные поля: номер/тип чека — полезно держать
    check_number = item.get("checkNumber") or item.get("check_number")
    check_type = item.get("checkType") or item.get("check_type")

    with transaction.atomic():
        obj, created = Paycheck.objects.update_or_create(
            paycheck_id=paycheck_id,
            defaults={**defaults, "check_number": check_number, "check_type": check_type}
        )

        # удаляем старые компоненты и создаём новые из earnings/deductions/taxes
        PaycheckComponent.objects.filter(paycheck=obj).delete()
        comps_to_create = []

        def _create_components(list_items, comp_type):
            for c in (list_items or []):
                # сохраняем ключевые поля из компонента; не вычисляем ничего
                comp = PaycheckComponent(
                    paycheck=obj,
                    component_id=c.get("componentId"),
                    check_component_id=c.get("checkComponentId"),
                    name=c.get("name"),
                    component_type=comp_type,
                    classification_type=c.get("classificationType"),
                    amount=_to_decimal_safe(c.get("amount") or c.get("value")),
                    rate=_to_decimal_safe(c.get("rate")) if c.get("rate") is not None else None,
                    hours=_to_decimal_safe(c.get("hours")) if c.get("hours") is not None else None,
                    labor_assignment_id=c.get("laborAssignmentId"),
                    organization_id=(c.get("organization") or {}).get("organizationId") if isinstance(c.get("organization"), dict) else None,
                    organization_name=(c.get("organization") or {}).get("name") if isinstance(c.get("organization"), dict) else None,
                    raw_json=c
                )
                comps_to_create.append(comp)

        # earnings -> EARNING, deductions -> DEDUCTION, taxes -> TAX
        _create_components(item.get("earnings"), "EARNING")
        _create_components(item.get("deductions"), "DEDUCTION")
        _create_components(item.get("taxes"), "TAX")

        if comps_to_create:
            PaycheckComponent.objects.bulk_create(comps_to_create)

    return obj


def sync_checks_for_payperiod(payperiod_id: str, company_id: str = None, page_limit: int = 100):
    """
    Простой синк чеков по payperiod. page_limit=100 — работает лучше на твоём API.
    """
    api = PaychexAPI()
    api.authenticate()

    if company_id is None:
        company_id = getattr(settings, "PAYCHEX_COMPANY_ID", None)

    offset = 0
    processed = 0

    while True:
        resp = api.get_companies_checks(company_id=company_id, pay_period_id=payperiod_id, offset=offset, limit=page_limit, filter_by_user_id=False)

        # import json
        # formatted_result = json.dumps(resp, indent=4, ensure_ascii=False)
        # print(formatted_result)
        # exit()
        
        if not isinstance(resp, dict):
            print("Unexpected response shape:", type(resp))
            break

        content = resp.get("content") or []
        if not content:
            break

        for item in content:
            try:
                upsert_paycheck_from_item(item, company_id=company_id)
                processed += 1
            except Exception as e:
                print(f"Failed to save paycheck {item.get('paycheckId') or item.get('checkId')}: {e}")

        # пагинация
        meta = resp.get("metadata") or {}
        pagination = (meta or {}).get("pagination") or {}
        if pagination:
            step = pagination.get("limit") or page_limit
            offset = pagination.get("offset", offset) + step
            total = pagination.get("total")
            if total and offset >= total:
                break
        else:
            break

    print(f"Processed {processed} checks for payperiod {payperiod_id}")
    return processed
