from __future__ import annotations

import base64
import json
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.core.management.base import BaseCommand


def _basic_auth_header(username: str, app_password: str) -> str:
    token = base64.b64encode(f"{username}:{app_password}".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"


def _get_json(url: str, headers: Dict[str, str], params: Optional[Dict[str, Any]] = None) -> Any:
    r = requests.get(url, headers=headers, params=params, timeout=60)
    # Helpful debug on failures
    if r.status_code >= 400:
        raise requests.HTTPError(
            f"{r.status_code} {r.reason} for url: {r.url}\n"
            f"Response body (first 500 chars): {r.text[:500]}",
            response=r,
        )
    return r.json()


class Command(BaseCommand):
    help = "One-way sync: pull LearnDash progress into Django (read-only)."

    def handle(self, *args, **options):
        base = (settings.LEARNDASH_BASE_URL or "").rstrip("/")
        user = settings.LEARNDASH_USERNAME
        pw = settings.LEARNDASH_APP_PASSWORD

        if not base or not user or not pw:
            raise SystemExit("Missing LEARNDASH_BASE_URL / LEARNDASH_USERNAME / LEARNDASH_APP_PASSWORD in env.")

        headers = {
            "Authorization": _basic_auth_header(user, pw),
            "Accept": "application/json",
            "User-Agent": "Django-LearnDash-Sync/1.0",
        }

        # ✅ Correct LearnDash courses route on this site
        ld_url = f"{base}/wp-json/ldlms/v1/sfwd-courses"
        courses = _get_json(ld_url, headers=headers, params={"per_page": 1})

        self.stdout.write(self.style.SUCCESS("Connected. LearnDash courses endpoint works."))
        self.stdout.write(json.dumps(courses, indent=2)[:1500])
