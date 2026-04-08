# integrations/ghl_client.py
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.utils import timezone

from .models import GHLAuth

API_BASE = "https://services.leadconnectorhq.com"
TOKEN_URL = f"{API_BASE}/oauth/token"

# LeadConnector requires this header for most endpoints
API_VERSION_HEADER_VALUE = "2021-07-28"


class GHLNotConnected(Exception):
    """Raised when OAuth tokens haven't been saved yet."""


def _configured_location_id() -> str:
    return (getattr(settings, "GHL_LOCATION_ID", "") or "").strip()


def _get_auth(location_id: Optional[str] = None) -> GHLAuth:
    requested_location_id = (location_id or _configured_location_id()).strip()
    if requested_location_id:
        auth = (
            GHLAuth.objects.filter(location_id=requested_location_id)
            .order_by("-updated_at")
            .first()
        )
        if not auth:
            raise GHLNotConnected(
                f"GHLAuth record missing for location {requested_location_id}. "
                "Complete OAuth at /oauth/start/ for that location."
            )
        return auth

    auth = GHLAuth.objects.order_by("-updated_at").first()
    if not auth:
        raise GHLNotConnected("GHLAuth record missing. Complete OAuth at /oauth/start/.")
    return auth


def get_auth(location_id: Optional[str] = None) -> GHLAuth:
    return _get_auth(location_id=location_id)


def _refresh(auth: GHLAuth) -> None:
    """
    Refresh the OAuth access token using refresh_token.
    """
    data = {
        "grant_type": "refresh_token",
        "client_id": settings.GHL_CLIENT_ID,
        "client_secret": settings.GHL_CLIENT_SECRET,
        "refresh_token": auth.refresh_token,
    }

    r = requests.post(TOKEN_URL, data=data, timeout=30)
    if r.status_code >= 400:
        raise requests.HTTPError(
            f"{r.status_code} Error refreshing token\nResponse: {r.text}",
            response=r,
        )

    p = r.json()
    expires_in = int(p.get("expires_in", 3600))

    auth.access_token = p["access_token"]
    auth.refresh_token = p.get("refresh_token", auth.refresh_token)
    auth.expires_at = timezone.now() + timedelta(seconds=expires_in - 60)

    # Keep existing location_id unless API returns a new one
    auth.location_id = p.get("locationId") or p.get("location_id") or auth.location_id
    auth.save(update_fields=["access_token", "refresh_token", "expires_at", "location_id"])


def get_access_token(location_id: Optional[str] = None) -> str:
    auth = _get_auth(location_id=location_id)
    if auth.is_expired():
        _refresh(auth)
    return auth.access_token


def request(
    method: str,
    endpoint: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    include_location_id: bool = True,
    location_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Unified GoHighLevel / LeadConnector API request helper.

    Features:
    - Auto refresh access token if expired
    - Adds required Version header
    - Optionally injects locationId into query/body (needed for many contacts endpoints)
    - Retries once on 401 (token might have been revoked/rotated)
    - Raises requests.HTTPError with response body for debugging

    Args:
      method: "GET", "POST", "PUT", "DELETE"
      endpoint: e.g. "/contacts/search"
      params: query string params
      json: JSON body
      include_location_id:
        - True (default): injects locationId if known
        - False: do NOT inject (use when locationId already in URL path or endpoint rejects it)

    Returns:
      Parsed JSON dict (or {} if empty response body)
    """
    auth = _get_auth(location_id=location_id)
    resolved_location_id = (location_id or auth.location_id or "").strip()

    headers = {
        "Authorization": f"Bearer {get_access_token(location_id=resolved_location_id or None)}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Version": API_VERSION_HEADER_VALUE,
    }

    merged_params: Dict[str, Any] = dict(params or {})
    if include_location_id and resolved_location_id:
        merged_params.setdefault("locationId", resolved_location_id)

    merged_json = json
    if include_location_id and isinstance(json, dict) and resolved_location_id:
        merged_json = dict(json)
        merged_json.setdefault("locationId", resolved_location_id)

    url = f"{API_BASE}{endpoint}"

    def _do_request() -> requests.Response:
        return requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=merged_params,
            json=merged_json,
            timeout=30,
        )

    r = _do_request()

    # If unauthorized, refresh once and retry
    if r.status_code == 401:
        _refresh(auth)
        headers["Authorization"] = f"Bearer {auth.access_token}"
        r = _do_request()

    if r.status_code >= 400:
        raise requests.HTTPError(
            f"{r.status_code} Error calling {url}\nResponse: {r.text}",
            response=r,
        )

    return r.json() if r.content else {}
