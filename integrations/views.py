# integrations/views.py
from __future__ import annotations

import requests
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils import timezone

from .models import GHLAuth

# Sub-account (Location) install flow
AUTH_URL = "https://marketplace.gohighlevel.com/oauth/chooselocation"

# Token exchange endpoint
TOKEN_URL = "https://services.leadconnectorhq.com/oauth/token"

# Scopes (must match what you enabled in Marketplace)
SCOPE = (
    "contacts.readonly contacts.write "
    "locations.readonly "
    "locations/customFields.readonly locations/customFields.write "
    "locations/customValues.write"
)


def ghl_oauth_start(request):
    """
    Redirect to GoHighLevel Marketplace OAuth install (choose a Location).
    """
    params = {
        "response_type": "code",
        "redirect_uri": settings.GHL_REDIRECT_URI,
        "client_id": settings.GHL_CLIENT_ID,
        "scope": SCOPE,
        "version_id": settings.GHL_VERSION_ID,  # REQUIRED for marketplace apps
    }
    return redirect(f"{AUTH_URL}?{urlencode(params)}")


def _ghl_location_dashboard_url(location_id: str) -> str:
    """
    Deep-link into the selected sub-account dashboard.
    Common pattern:
      https://app.gohighlevel.com/v2/location/<locationId>/dashboard
    """
    location_id = (location_id or "").strip()
    if not location_id:
        return "https://app.gohighlevel.com/"
    return f"https://app.gohighlevel.com/v2/location/{location_id}/dashboard"


def ghl_oauth_callback(request):
    """
    OAuth callback endpoint. Exchanges ?code=... for tokens and stores them in DB.
    Then redirects into the selected sub-account (Option B).
    """
    code = request.GET.get("code")
    if not code:
        return HttpResponseBadRequest("Missing ?code parameter from GoHighLevel")

    data = {
        "grant_type": "authorization_code",
        "client_id": settings.GHL_CLIENT_ID,
        "client_secret": settings.GHL_CLIENT_SECRET,
        "redirect_uri": settings.GHL_REDIRECT_URI,
        "code": code,
    }

    r = requests.post(TOKEN_URL, data=data, timeout=30)

    # If token exchange fails, show the real reason (instead of 500)
    if r.status_code >= 400:
        return HttpResponse(
            "❌ Token exchange failed<br><br>"
            f"Status: {r.status_code}<br>"
            f"Response: <pre>{r.text}</pre><br><br>"
            "Most common causes:<br>"
            "1) client_secret wrong / not loaded on server<br>"
            "2) redirect_uri mismatch (must match EXACTLY incl trailing /)<br>"
            "3) code already used/expired (try OAuth again)<br>",
            status=400,
        )

    p = r.json()

    expires_in = int(p.get("expires_in", 3600))
    expires_at = timezone.now() + timedelta(seconds=expires_in - 60)

    location_id = p.get("locationId") or p.get("location_id") or ""

    defaults = {
        "access_token": p["access_token"],
        "refresh_token": p["refresh_token"],
        "expires_at": expires_at,
        "location_id": location_id,
    }

    # Save OAuth tokens per chosen Location when possible so multiple sub-accounts
    # can coexist in Django instead of overwriting one shared singleton row.
    if location_id:
        GHLAuth.objects.update_or_create(
            location_id=location_id,
            defaults=defaults,
        )
    else:
        GHLAuth.objects.update_or_create(
            id=1,
            defaults=defaults,
        )

    # ✅ Option B: redirect user into the selected GHL sub-account dashboard
    return redirect(_ghl_location_dashboard_url(location_id))
