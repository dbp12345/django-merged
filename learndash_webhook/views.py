from __future__ import annotations

import hmac
import json
from typing import Any, Dict, Optional

from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import JsonResponse, HttpRequest
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt

from .models import (
    LearndashUser,
    LearndashCourse,
    LearndashLessonCompletion,
    LearndashCourseCompletion,
)


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"ok": False, "error": message}, status=status)


def _parse_dt(value: Any) -> timezone.datetime:
    """
    Accepts ISO strings like:
      - 2026-02-10T12:00:00Z
      - 2026-02-10T12:00:00+00:00
      - 2026-02-10T12:00:00 (naive)
    Falls back to now if missing/invalid.
    """
    if not value:
        return timezone.now()

    if isinstance(value, str):
        dt = parse_datetime(value.replace("Z", "+00:00"))
        if not dt:
            return timezone.now()
        if timezone.is_naive(dt):
            # assume server timezone if naive
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    return timezone.now()


def _clean_email(value: Any) -> str:
    return str(value or "").strip().lower()


@csrf_exempt
def learndash_webhook(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return _json_error("POST required", 405)

    expected = getattr(settings, "LD_WEBHOOK_SECRET", "")
    provided = request.headers.get("X-LD-Secret", "")

    if not expected:
        return _json_error("Server misconfig: LD_WEBHOOK_SECRET not set", 500)

    if not hmac.compare_digest(provided, expected):
        return _json_error("Unauthorized", 401)

    raw = request.body or b""
    try:
        payload: Dict[str, Any] = json.loads(raw.decode("utf-8"))
    except Exception:
        return _json_error("Invalid JSON", 400)

    event_type = str(payload.get("event_type", "")).strip()
    if event_type not in {"lesson_completed", "course_completed"}:
        return _json_error("event_type must be lesson_completed or course_completed", 400)

    wp_user_id = payload.get("wp_user_id")
    wp_course_id = payload.get("wp_course_id") or payload.get("course_id")

    if not wp_user_id:
        return _json_error("Missing wp_user_id", 400)
    if not wp_course_id:
        return _json_error("Missing wp_course_id/course_id", 400)

    try:
        wp_user_id = int(wp_user_id)
        wp_course_id = int(wp_course_id)
    except Exception:
        return _json_error("wp_user_id/wp_course_id must be integers", 400)

    user_email = _clean_email(payload.get("user_email"))
    course_name = str(payload.get("course_name", "")).strip()
    completed_at = _parse_dt(payload.get("completed_at"))

    with transaction.atomic():
        # --- User upsert (don’t wipe email with blank) ---
        user, created_user = LearndashUser.objects.get_or_create(
            wp_user_id=wp_user_id,
            defaults={"email": user_email},
        )
        if (not created_user) and user_email and user.email != user_email:
            user.email = user_email
            user.save(update_fields=["email"])

        # --- Course upsert ---
        course, created_course = LearndashCourse.objects.get_or_create(
            wp_course_id=wp_course_id,
            defaults={"name": course_name or f"Course {wp_course_id}"},
        )
        # ✅ update if changed and provided
        if (not created_course) and course_name and course.name != course_name:
            course.name = course_name
            course.save(update_fields=["name"])

        # --- Lesson completed ---
        if event_type == "lesson_completed":
            wp_lesson_id = payload.get("wp_lesson_id") or payload.get("lesson_id")
            lesson_name = str(payload.get("lesson_name", "")).strip()

            if not wp_lesson_id:
                return _json_error("Missing wp_lesson_id/lesson_id for lesson_completed", 400)

            try:
                wp_lesson_id = int(wp_lesson_id)
            except Exception:
                return _json_error("wp_lesson_id must be an integer", 400)

            try:
                LearndashLessonCompletion.objects.create(
                    user=user,
                    course=course,
                    wp_lesson_id=wp_lesson_id,
                    lesson_name=lesson_name or f"Lesson {wp_lesson_id}",
                    completed_at=completed_at,
                )
                created = True
            except IntegrityError:
                created = False

            return JsonResponse(
                {"ok": True, "saved": "lesson_completed", "created": created},
                status=200,
            )

        # --- Course completed ---
        try:
            LearndashCourseCompletion.objects.create(
                user=user,
                course=course,
                completed_at=completed_at,
            )
            created = True
        except IntegrityError:
            created = False

        return JsonResponse(
            {"ok": True, "saved": "course_completed", "created": created},
            status=200,
        )
