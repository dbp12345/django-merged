from typing import Dict, Any

from django.conf import settings
from django.db import transaction
from django.db.models import F, Value
from django.db.models.functions import Replace

from company.models import Employees_Parameters
from paychex.models import CompanyWorkers
from paychex.services.PaychexAPIService import PaychexAPI
from core.services.SanitazerService import SanitazerService


def upsert_company_worker_from_api(item: Dict[str, Any]) -> CompanyWorkers:
    worker_id = item.get("workerId")
    if not worker_id:
        raise ValueError("incoming worker object has no workerId")

    name = item.get("name") or {}
    legal = item.get("legalId") or {}
    organization = item.get("organization") or {}
    current_status = item.get("currentStatus") or {}

    legal_id_type = legal.get("legalIdType")
    legal_id_value = legal.get("legalIdValue")
    # приведение к строке — важно для поиска и хранения
    legal_id_value_str = str(legal_id_value) if legal_id_value is not None else None

    defaults = {
        "company_id": settings.PAYCHEX_COMPANY_ID,
        "employee_id": item.get("employeeId"),
        "worker_type": item.get("workerType"),
        "exemption_type": item.get("exemptionType"),
        "work_state": item.get("workState"),
        "birth_date": SanitazerService.parse_iso_date_to_date(item.get("birthDate")),
        "sex": item.get("sex"),
        "hire_date": SanitazerService.parse_iso_date_to_date(item.get("hireDate")),
        "family_name": name.get("familyName"),
        "middle_name": name.get("middleName"),
        "given_name": name.get("givenName"),
        "legal_id_type": legal_id_type,
        "legal_id_value": legal_id_value_str,
        "labor_assignment_id": item.get("laborAssignmentId"),
        "location_id": item.get("locationId"),
        "organization_id": organization.get("organizationId"),
        "organization_name": organization.get("name"),
        "organization_number": organization.get("number"),
        "worker_status_id": current_status.get("workerStatusId"),
        "status_type": current_status.get("statusType"),
        "status_reason": current_status.get("statusReason"),
        "status_effective_date": SanitazerService.parse_iso_date_to_date(current_status.get("effectiveDate")),
        "raw_json": item,
    }

    found_employee = None
    if isinstance(legal_id_type, str) and legal_id_type.lower() == "ssn" and legal_id_value_str:
        try:
            clean_input = "".join(ch for ch in legal_id_value_str if ch.isdigit())
            # param = Employees_Parameters.objects.select_related("contacts_prop", "employee").filter(
            #     contacts_prop__property_name="Social Security Number",
            #     value=legal_id_value_str
            # ).first()
            param = (
                Employees_Parameters.objects
                .select_related("contacts_prop", "employee")
                .filter(contacts_prop__property_name="Social Security Number")
                .annotate(clean_value=Replace(F("value"), Value("-"), Value("")))
                .filter(clean_value=clean_input)
                .first()
            )
            if param:
                found_employee = getattr(param, "employee", None)
        except Exception:
            found_employee = None

    with transaction.atomic():
        obj = CompanyWorkers.objects.filter(worker_id=worker_id).first()
        if obj is None:
            if found_employee:
                defaults["employees"] = found_employee
            obj = CompanyWorkers.objects.create(worker_id=worker_id, **defaults)
        else:
            update_fields = []
            for k, v in defaults.items():
                # raw_json всегда перезаписываем, остальные поля тоже перезаписываем
                setattr(obj, k, v)
                update_fields.append(k)

            # если у записи нет employees и мы нашли employee — установим
            if getattr(obj, "employees_id", None) is None and found_employee:
                obj.employees = found_employee
                update_fields.append("employees")

            if update_fields:
                obj.save(update_fields=list(set(update_fields)) + ["updated_at"])

    return obj

# def sync_company_workers_from_api(company_id=None, from_date=None, to_date=None):
#     api = PaychexAPI()
#     api.authenticate()
#     processed = 0
#
#     resp = api.get_company_workers(company_id=company_id, from_date=from_date, to_date=to_date)
#
#     # ожидаем обёртку {"metadata":..., "content":[...], ...}
#     content = resp.get("content") if isinstance(resp, dict) else None
#
#     for item in content:
#         upsert_company_worker_from_api(item)
#         processed += 1
#         print(f"Processed {processed} workers...")
#
#     print("Sync finished. Total processed:", processed)
#     return processed

def sync_company_workers_from_api(company_id=None, from_date=None, to_date=None):
    api = PaychexAPI()
    api.authenticate()
    processed = 0

    if from_date or to_date:
        resp = api.get_company_workers(
            company_id=company_id,
            from_date=from_date,
            to_date=to_date,
        )
        if isinstance(resp, dict):
            content = resp.get("content") or []
            errors = resp.get("errors", None)
            # If server returned something plausible — use it and finish
            if content:
                for item in content:
                    upsert_company_worker_from_api(item)
                    processed += 1
                print("Used server-side date filter. Processed:", processed)

            if errors:
                print("Errors:", errors)

        return processed

    offset = 0
    limit = 100

    # Pagination loop using offset/limit
    while True:
        resp = api.get_company_workers(
            company_id=company_id,
            from_date=from_date,
            to_date=to_date,
            offset=offset,
            limit=limit,
        )

        if not isinstance(resp, dict):
            print(f"Unexpected response type at offset {offset}: {type(resp)}")
            break

        # Log API errors if present
        errors = resp.get("errors")
        if errors:
            print(f"API errors at offset {offset}: {errors}")

        content = resp.get("content") or []

        if not content:
            # no more records
            break

        for item in content:
            upsert_company_worker_from_api(item)
            processed += 1
            if processed % 50 == 0:
                print(f"Processed {processed} workers...")

        offset += limit

    print("Sync finished. Total processed:", processed)
    return processed
