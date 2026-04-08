# integrations/ghl_sync.py
from __future__ import annotations

import hashlib
import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from companies.models import Company
from contacts.models import Contact
from integrations.ghl_client import GHLNotConnected, get_auth, request
from integrations.models import GHLContactSyncMeta

logger = logging.getLogger(__name__)

# -----------------------------
# Loop-prevention flag (threadlocal)
# -----------------------------
_SYNC_LOCAL = threading.local()


def disable_sync() -> None:
    _SYNC_LOCAL.disabled = True


def enable_sync() -> None:
    _SYNC_LOCAL.disabled = False


def is_sync_disabled() -> bool:
    return bool(getattr(_SYNC_LOCAL, "disabled", False))


# -----------------------------
# Defaults for contacts created from GHL
# -----------------------------
def _get_default_company() -> Company:
    """
    Contact.company is required in Django.
    For contacts created from GHL, attach them to a default Company.
    """
    name = getattr(settings, "GHL_DEFAULT_COMPANY_NAME", None) or "Dust Busters Plus LLC"
    company, _ = Company.objects.get_or_create(name=name)
    return company


def _default_role() -> str:
    return getattr(settings, "GHL_DEFAULT_CONTACT_ROLE", "employee")


# -----------------------------
# Field mapping (standard fields)
# -----------------------------
SYNCED_DJANGO_FIELDS = ("first_name", "last_name", "email", "phone", "company", "role")
SYNCED_GHL_FIELDS = ("firstName", "lastName", "email", "phone")


def _norm_email(email: Optional[str]) -> str:
    return (email or "").strip().lower()


def _safe_str(v: Any) -> str:
    return (v or "").strip() if isinstance(v, str) else ("" if v is None else str(v))


def _hash_payload(payload: Dict[str, Any]) -> str:
    """
    Stable hash for comparing "synced fields" and preventing loops.
    NOTE: We hash the outbound payload (including customFields) so company/role changes
          will be detected even though they are stored in GHL custom fields.
    """
    items = sorted((k, _safe_str(payload.get(k))) for k in payload.keys())
    raw = "|".join(f"{k}={v}" for k, v in items)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _parse_ghl_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if timezone.is_aware(value) else timezone.make_aware(value)
    if isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(float(value))
        return timezone.make_aware(dt)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt if timezone.is_aware(dt) else timezone.make_aware(dt)
        except Exception:
            return None
    return None


def _ghl_updated_at(gc: Dict[str, Any]) -> Optional[datetime]:
    for key in ("updatedAt", "updated_at", "dateUpdated", "date_updated", "lastUpdated", "last_updated"):
        if key in gc:
            dt = _parse_ghl_datetime(gc.get(key))
            if dt:
                return dt
    return None


def _extract_custom_field_value(gc: Dict[str, Any], field_id: str) -> Optional[str]:
    cf = gc.get("customFields")
    if not cf:
        return None
    if isinstance(cf, list):
        for item in cf:
            if isinstance(item, dict) and item.get("id") == field_id:
                v = item.get("value")
                return str(v) if v is not None else None
    if isinstance(cf, dict):
        v = cf.get(field_id)
        return str(v) if v is not None else None
    return None


def _custom_fields_payload_for_contact(c: Contact) -> List[Dict[str, str]]:
    """
    Custom fields written to GHL:
      - Django Contact ID (required)
      - Company name (optional if configured)
      - Role (optional if configured)
    """
    payload: List[Dict[str, str]] = []

    # Required: Django contact ID
    id_field = getattr(settings, "GHL_DJANGO_CONTACT_ID_FIELD_ID", None)
    if not id_field:
        raise RuntimeError("Missing settings.GHL_DJANGO_CONTACT_ID_FIELD_ID")
    payload.append({"id": id_field, "value": str(c.id)})

    # Optional: company name -> GHL custom field
    company_field = getattr(settings, "GHL_DJANGO_COMPANY_FIELD_ID", None)
    if company_field:
        company_name = ""
        try:
            company_name = getattr(c.company, "name", "") or ""
        except Exception:
            company_name = ""
        payload.append({"id": company_field, "value": company_name})

    # Optional: role -> GHL custom field
    role_field = getattr(settings, "GHL_DJANGO_ROLE_FIELD_ID", None)
    if role_field:
        payload.append({"id": role_field, "value": (c.role or "")})

    return payload


def _payload_for_create(c: Contact) -> Dict[str, Any]:
    # POST /contacts/ — locationId allowed/required
    location_id = getattr(settings, "GHL_LOCATION_ID", None)  # fallback; request() also injects auth.location_id
    return {
        "firstName": c.first_name or "",
        "lastName": c.last_name or "",
        "email": c.email or "",
        "phone": c.phone or "",
        "locationId": (location_id or ""),
        "customFields": _custom_fields_payload_for_contact(c),
    }


def _payload_for_update(c: Contact) -> Dict[str, Any]:
    # PUT /contacts/{id} — locationId MUST NOT exist
    return {
        "firstName": c.first_name or "",
        "lastName": c.last_name or "",
        "email": c.email or "",
        "phone": c.phone or "",
        "customFields": _custom_fields_payload_for_contact(c),
    }


def _ghl_find_by_email(email: str) -> Optional[Dict[str, Any]]:
    email = _norm_email(email)
    if not email:
        return None
    data = request(
        "POST",
        "/contacts/search",
        json={"query": email, "page": 1, "pageLimit": 1},
    )
    contacts = data.get("contacts") or data.get("data") or data.get("results") or []
    return contacts[0] if contacts else None


def _is_contact_not_found_error(exc: Exception) -> bool:
    resp = getattr(exc, "response", None)
    if not resp:
        return False
    try:
        j = resp.json()
        msg = (j.get("message") or "")
    except Exception:
        msg = (getattr(resp, "text", "") or "")
    return "Contact not found for id" in msg


def _duplicate_existing_contact_id(exc: Exception) -> Optional[str]:
    resp = getattr(exc, "response", None)
    if not resp:
        return None
    try:
        j = resp.json()
    except Exception:
        return None
    msg = (j.get("message") or "")
    if j.get("statusCode") == 400 and "duplicated" in msg.lower():
        meta = j.get("meta") or {}
        return meta.get("contactId")
    return None


def _get_or_create_meta(c: Contact) -> GHLContactSyncMeta:
    meta, _ = GHLContactSyncMeta.objects.get_or_create(contact=c)
    return meta


def _django_changed_since_last_sync(c: Contact, meta: GHLContactSyncMeta) -> bool:
    last_synced = meta.last_synced_at
    if not last_synced:
        return True
    if hasattr(c, "updated_at") and c.updated_at:
        return c.updated_at > last_synced

    current_hash = _hash_payload(_payload_for_update(c))
    return (meta.sync_hash or "") != current_hash


def _prefer_django_on_conflict(*, django_changed: bool, ghl_changed: bool) -> bool:
    # Prefer Django ONLY when BOTH changed since last sync.
    return bool(django_changed and ghl_changed)


# -----------------------------
# Core operations
# -----------------------------
@dataclass
class PullResult:
    created: int = 0
    updated: int = 0
    linked: int = 0
    skipped: int = 0
    conflicts_pref_django: int = 0


@dataclass
class PushResult:
    pushed: int = 0
    created: int = 0
    relinked: int = 0
    skipped: int = 0


def pull_ghl_to_django(
    *,
    page_limit: int = 100,
    max_pages: int = 500,
    changed_since: Optional[datetime] = None,
    dry_run: bool = False,
) -> PullResult:
    """
    Poll GHL and apply changes into Django.

    - Match by email (primary)
    - If missing, fallback by Django ID stored in your custom field (secondary)
    - If both sides changed since last sync -> keep Django values (conflict strategy)
    - Otherwise, apply GHL values to Django (first/last/phone only)
    """
    res = PullResult()

    django_id_field = getattr(settings, "GHL_DJANGO_CONTACT_ID_FIELD_ID", None)
    if not django_id_field:
        raise RuntimeError("Missing settings.GHL_DJANGO_CONTACT_ID_FIELD_ID")

    page = 1
    while page <= max_pages:
        data = request(
            "POST",
            "/contacts/search",
            json={"page": int(page), "pageLimit": int(page_limit)},
        )
        contacts = data.get("contacts") or data.get("data") or data.get("results") or []
        if not contacts:
            break

        for gc in contacts:
            ghl_id = gc.get("id") or gc.get("_id")
            email = _norm_email(gc.get("email"))

            if not ghl_id or not email:
                res.skipped += 1
                continue

            ghl_updated = _ghl_updated_at(gc)

            if changed_since and ghl_updated and ghl_updated <= changed_since:
                continue

            # 1) match by email
            dj = Contact.objects.filter(email__iexact=email).first()

            # 2) fallback match by django-id stored in custom field
            if not dj:
                ghl_dj_id = _extract_custom_field_value(gc, django_id_field)
                if ghl_dj_id and ghl_dj_id.isdigit():
                    dj = Contact.objects.filter(id=int(ghl_dj_id)).first()

            if not dj:
                # Create in Django (company + role required)
                if dry_run:
                    res.created += 1
                    continue

                default_company = _get_default_company()
                dj = Contact.objects.create(
                    company=default_company,
                    role=_default_role(),
                    email=email,
                    first_name=gc.get("firstName", "") or "",
                    last_name=gc.get("lastName", "") or "",
                    phone=gc.get("phone", "") or "",
                    privser_contact_id=ghl_id,
                )
                meta = _get_or_create_meta(dj)
                meta.ghl_last_modified_at = ghl_updated
                meta.last_synced_at = timezone.now()
                meta.sync_hash = _hash_payload(_payload_for_update(dj))
                meta.save()
                res.created += 1
                continue

            # Ensure link stored on Django contact
            if getattr(dj, "privser_contact_id", None) != ghl_id:
                if not dry_run:
                    Contact.objects.filter(pk=dj.pk).update(privser_contact_id=ghl_id, updated_at=timezone.now())
                res.linked += 1
                dj.privser_contact_id = ghl_id

            meta = _get_or_create_meta(dj)

            django_changed = _django_changed_since_last_sync(dj, meta)

            ghl_changed = False
            if ghl_updated and meta.ghl_last_modified_at:
                ghl_changed = ghl_updated > meta.ghl_last_modified_at
            elif ghl_updated and not meta.ghl_last_modified_at:
                ghl_changed = True

            if _prefer_django_on_conflict(django_changed=django_changed, ghl_changed=ghl_changed):
                if not dry_run:
                    meta.ghl_last_modified_at = ghl_updated or meta.ghl_last_modified_at
                    meta.save(update_fields=["ghl_last_modified_at", "updated_at"])
                res.conflicts_pref_django += 1
                continue

            # Apply standard fields (first/last/phone). Email is identity => do not overwrite.
            new_first = (gc.get("firstName") or "").strip()
            new_last = (gc.get("lastName") or "").strip()
            new_phone = (gc.get("phone") or "").strip()

            changes: Dict[str, Any] = {}
            if new_first != (dj.first_name or "").strip():
                changes["first_name"] = new_first
            if new_last != (dj.last_name or "").strip():
                changes["last_name"] = new_last
            if new_phone != (dj.phone or "").strip():
                changes["phone"] = new_phone

            if changes:
                if dry_run:
                    res.updated += 1
                else:
                    disable_sync()
                    try:
                        with transaction.atomic():
                            changes["updated_at"] = timezone.now()
                            Contact.objects.filter(pk=dj.pk).update(**changes)

                            dj.first_name = changes.get("first_name", dj.first_name)
                            dj.last_name = changes.get("last_name", dj.last_name)
                            dj.phone = changes.get("phone", dj.phone)

                            meta.ghl_last_modified_at = ghl_updated or meta.ghl_last_modified_at
                            meta.last_synced_at = timezone.now()
                            meta.sync_hash = _hash_payload(_payload_for_update(dj))
                            meta.save(update_fields=["ghl_last_modified_at", "last_synced_at", "sync_hash", "updated_at"])
                    finally:
                        enable_sync()
                    res.updated += 1
            else:
                if not dry_run and ghl_updated:
                    meta.ghl_last_modified_at = ghl_updated
                    meta.save(update_fields=["ghl_last_modified_at", "updated_at"])

        has_more = len(contacts) >= page_limit
        if not has_more:
            break
        page += 1

    return res


def push_django_to_ghl(*, queryset=None) -> PushResult:
    """
    Push Django changes to GHL.

    - Uses email as primary lookup
    - Uses Contact.privser_contact_id when available
    - Skips if hash unchanged
    - Company/Role changes are pushed via customFields (if configured)
    """
    res = PushResult()
    qs = queryset or Contact.objects.exclude(email="").exclude(email__isnull=True)

    try:
        active_auth = get_auth()
    except GHLNotConnected:
        logger.exception("push_django_to_ghl aborted because no active GHL auth is configured")
        return res

    if active_auth.is_read_only():
        skipped_count = qs.count() if hasattr(qs, "count") else 0
        res.skipped += skipped_count
        logger.info(
            "push_django_to_ghl skipped because location %s is configured read-only",
            active_auth.location_id,
        )
        return res

    for c in qs.iterator():
        try:
            if not c.email:
                res.skipped += 1
                continue

            meta = _get_or_create_meta(c)
            payload_u = _payload_for_update(c)
            current_hash = _hash_payload(payload_u)

            if meta.sync_hash and meta.sync_hash == current_hash:
                res.skipped += 1
                continue

            ghl_id = getattr(c, "privser_contact_id", None)

            if ghl_id:
                try:
                    request("PUT", f"/contacts/{ghl_id}", json=payload_u, include_location_id=False)
                    meta.last_synced_at = timezone.now()
                    meta.sync_hash = current_hash
                    meta.save(update_fields=["last_synced_at", "sync_hash", "updated_at"])
                    res.pushed += 1
                    continue
                except Exception as e:
                    if _is_contact_not_found_error(e):
                        Contact.objects.filter(pk=c.pk).update(privser_contact_id=None, updated_at=timezone.now())
                        c.privser_contact_id = None
                        ghl_id = None
                    else:
                        raise

            found = _ghl_find_by_email(c.email)
            if found:
                found_id = found.get("id") or found.get("_id")
                if found_id:
                    Contact.objects.filter(pk=c.pk).update(privser_contact_id=found_id, updated_at=timezone.now())
                    c.privser_contact_id = found_id

                    request("PUT", f"/contacts/{found_id}", json=payload_u, include_location_id=False)

                    meta.last_synced_at = timezone.now()
                    meta.sync_hash = current_hash
                    meta.save(update_fields=["last_synced_at", "sync_hash", "updated_at"])
                    res.relinked += 1
                    res.pushed += 1
                    continue

            payload_c = _payload_for_create(c)
            try:
                resp = request("POST", "/contacts/", json=payload_c, include_location_id=True)
                new_id = (resp.get("contact") or {}).get("id") or resp.get("id")
                if new_id:
                    Contact.objects.filter(pk=c.pk).update(privser_contact_id=new_id, updated_at=timezone.now())
                    meta.last_synced_at = timezone.now()
                    meta.sync_hash = current_hash
                    meta.save(update_fields=["last_synced_at", "sync_hash", "updated_at"])
                    res.created += 1
                    res.pushed += 1
            except Exception as e:
                existing_id = _duplicate_existing_contact_id(e)
                if existing_id:
                    Contact.objects.filter(pk=c.pk).update(privser_contact_id=existing_id, updated_at=timezone.now())
                    request("PUT", f"/contacts/{existing_id}", json=payload_u, include_location_id=False)

                    meta.last_synced_at = timezone.now()
                    meta.sync_hash = current_hash
                    meta.save(update_fields=["last_synced_at", "sync_hash", "updated_at"])
                    res.relinked += 1
                    res.pushed += 1
                else:
                    raise

        except Exception:
            logger.exception("push_django_to_ghl failed for %s", getattr(c, "email", None))

    return res
