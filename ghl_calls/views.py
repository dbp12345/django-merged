from __future__ import annotations

import json
import logging
from typing import Any, Dict
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import (
    Answer,
    CallNote,
    GHLCall,
    Question,
    Statement,
    UnifiedNodeAnswer,
    UnifiedNodeQuestion,
    UnifiedNodeQuestionAlias,
    UnifiedNodeStatement,
)
from .services import (
    auto_group_questions,
    ensure_unified_question_alias,
    find_best_segment_for_span,
    is_call_event,
    suggest_unified_questions,
    store_call_event,
    upsert_transcript_from_workflow,
    verify_webhook_signature,
)

logger = logging.getLogger(__name__)


SEGMENT_KIND_CONFIG = {
    "question": {
        "model": Question,
        "label": "Questions",
        "singular": "question",
        "node_model": UnifiedNodeQuestion,
        "node_field": "unified_question",
        "node_label": "Unified Question",
        "node_placeholder": "Canonical question to assign",
        "search_fields": (
            "text",
            "call__ghl_call_id",
            "call__call_sid",
            "call__ghl_location_id",
            "unified_question__name",
        ),
        "select_related": ("call", "unified_question"),
    },
    "answer": {
        "model": Answer,
        "label": "Answers",
        "singular": "answer",
        "node_model": UnifiedNodeAnswer,
        "node_field": "unified_answer",
        "node_label": "Unified Answer",
        "node_placeholder": "Canonical answer to assign",
        "search_fields": (
            "text",
            "question__text",
            "call__ghl_call_id",
            "call__call_sid",
            "call__ghl_location_id",
            "unified_answer__name",
        ),
        "select_related": ("call", "question", "unified_answer"),
    },
    "statement": {
        "model": Statement,
        "label": "Statements",
        "singular": "statement",
        "node_model": UnifiedNodeStatement,
        "node_field": "unified_statement",
        "node_label": "Unified Statement",
        "node_placeholder": "Canonical statement to assign",
        "search_fields": (
            "text",
            "call__ghl_call_id",
            "call__call_sid",
            "call__ghl_location_id",
            "unified_statement__name",
        ),
        "select_related": ("call", "unified_statement"),
    },
}


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"ok": False, "error": message}, status=status)


def _normalize_segment_kind(kind: str) -> str:
    return kind if kind in SEGMENT_KIND_CONFIG else "question"


def _multiline_terms(value: str) -> list[str]:
    terms = [line.strip() for line in (value or "").replace("\r", "\n").split("\n")]
    return [term for term in terms if term]


def _build_segment_search_query(search_value: str, fields: tuple[str, ...]) -> Q:
    terms = _multiline_terms(search_value)
    if not terms:
        return Q()

    search_query = Q()
    for term in terms:
        term_query = Q()
        for field in fields:
            term_query |= Q(**{f"{field}__icontains": term})
        search_query |= term_query
    return search_query


def _segment_queryset(kind: str, search_value: str):
    config = SEGMENT_KIND_CONFIG[kind]
    queryset = config["model"].objects.select_related(*config["select_related"])
    search_query = _build_segment_search_query(search_value, config["search_fields"])
    if search_query:
        queryset = queryset.filter(search_query)
    return queryset.order_by("-call__created_at", "-call_id", "start_index", "id")


def _segment_row(kind: str, segment: Question | Answer | Statement) -> dict[str, Any]:
    call_label = getattr(segment.call, "call_sid", "") or getattr(segment.call, "ghl_call_id", "")
    if kind == "question":
        node_name = segment.unified_question.name if segment.unified_question_id else ""
        linked_context = ""
    elif kind == "answer":
        node_name = segment.unified_answer.name if segment.unified_answer_id else ""
        linked_context = segment.question.text if segment.question_id else ""
    else:
        node_name = segment.unified_statement.name if segment.unified_statement_id else ""
        linked_context = ""

    return {
        "id": segment.id,
        "text": segment.text,
        "speaker_role": segment.get_speaker_role_display(),
        "call_label": call_label,
        "call_admin_url": reverse("admin:ghl_calls_ghlcall_change", args=[segment.call_id]),
        "review_url": reverse("ghl_call_review", args=[segment.call_id]),
        "node_name": node_name,
        "linked_context": linked_context,
        "start_index": segment.start_index,
        "end_index": segment.end_index,
    }


def _bulk_editor_context(
    request: HttpRequest,
    *,
    kind: str,
    search_value: str,
    page_number: str | None,
    form_state: dict[str, str] | None = None,
    error_message: str = "",
) -> dict[str, Any]:
    config = SEGMENT_KIND_CONFIG[kind]
    queryset = _segment_queryset(kind, search_value)
    paginator = Paginator(queryset, 100)
    page_obj = paginator.get_page(page_number)
    query_base = urlencode({"kind": kind, "q": search_value})

    if form_state is None:
        form_state = {
            "find_text": "",
            "replacement_text": "",
        }

    updated_count = request.GET.get("updated", "").strip()

    return {
        "active_kind": kind,
        "active_config": config,
        "bulk_tabs": [
            {"key": key, "label": value["label"], "url": f"{reverse('ghl_call_bulk_edit')}?{urlencode({'kind': key, 'q': search_value})}"}
            for key, value in SEGMENT_KIND_CONFIG.items()
        ],
        "search_value": search_value,
        "page_obj": page_obj,
        "segment_rows": [_segment_row(kind, segment) for segment in page_obj.object_list],
        "form_state": form_state,
        "error_message": error_message,
        "success_message": (
            f"Updated {updated_count} {config['label'].lower()}."
            if updated_count
            else ""
        ),
        "query_base": query_base,
        "current_page": page_obj.number,
        "search_placeholder": f"Search {config['label'].lower()}... paste multiple lines from Excel",
    }


def _question_grouping_queryset(search_value: str, show_mode: str):
    queryset = Question.objects.select_related("call", "unified_question").prefetch_related("unified_question__aliases")
    if show_mode != "all":
        queryset = queryset.filter(unified_question__isnull=True)

    search_fields = (
        "text",
        "call__ghl_call_id",
        "call__call_sid",
        "unified_question__name",
        "unified_question__aliases__name",
    )
    search_query = _build_segment_search_query(search_value, search_fields)
    if search_query:
        queryset = queryset.filter(search_query).distinct()
    return queryset.order_by("-call__created_at", "-call_id", "start_index", "id")


def _question_grouping_rows(page_obj) -> list[dict[str, Any]]:
    rows = []
    for question in page_obj.object_list:
        suggestions = suggest_unified_questions(question.text)
        rows.append(
            {
                "question": question,
                "call_label": question.call.call_sid or question.call.ghl_call_id,
                "call_admin_url": reverse("admin:ghl_calls_ghlcall_change", args=[question.call_id]),
                "review_url": reverse("ghl_call_review", args=[question.call_id]),
                "suggestions": suggestions,
                "current_label": question.unified_question.name if question.unified_question_id else "",
                "alias_labels": list(question.unified_question.aliases.values_list("name", flat=True)) if question.unified_question_id else [],
            }
        )
    return rows


def _question_grouping_context(request: HttpRequest, *, search_value: str, show_mode: str, page_number: str | None):
    queryset = _question_grouping_queryset(search_value, show_mode)
    paginator = Paginator(queryset, 50)
    page_obj = paginator.get_page(page_number)
    query_base = urlencode({"q": search_value, "show": show_mode})
    return {
        "search_value": search_value,
        "show_mode": show_mode,
        "page_obj": page_obj,
        "query_base": query_base,
        "grouping_rows": _question_grouping_rows(page_obj),
        "unified_question_names": list(UnifiedNodeQuestion.objects.order_by("name").values_list("name", flat=True)[:500]),
    }


def _shift_index(value: int | None, threshold: int, delta: int) -> int | None:
    if value is None:
        return None
    if value >= threshold:
        return value + delta
    return value


def _replace_segment_text_for_call(
    *,
    call: GHLCall,
    selected_segments: list[Question | Answer | Statement],
    find_text: str,
    replacement_text: str,
) -> int:
    transcript_text = call.transcript_text or ""
    if not transcript_text:
        return 0

    all_segments: list[Question | Answer | Statement] = [
        *list(call.questions.all()),
        *list(call.answers.all()),
        *list(call.statements.all()),
    ]
    call_notes = list(call.notes.all())
    changed_count = 0
    selected_keys = {
        (segment.__class__, segment.pk)
        for segment in selected_segments
    }

    target_segments = [
        segment
        for segment in all_segments
        if (segment.__class__, segment.pk) in selected_keys
    ]

    for segment in sorted(
        target_segments,
        key=lambda item: (
            item.start_index if item.start_index is not None else 10**9,
            item.end_index if item.end_index is not None else 10**9,
            item.id,
        ),
    ):
        if segment.start_index is None or segment.end_index is None:
            continue
        if segment.start_index < 0 or segment.end_index < segment.start_index:
            continue

        current_span = transcript_text[segment.start_index:segment.end_index]
        if not current_span or find_text not in current_span:
            continue

        new_span = current_span.replace(find_text, replacement_text)
        if new_span == current_span:
            continue

        original_end = segment.end_index
        delta = len(new_span) - len(current_span)
        transcript_text = (
            transcript_text[:segment.start_index]
            + new_span
            + transcript_text[segment.end_index:]
        )

        segment.text = new_span
        segment.end_index = segment.start_index + len(new_span)
        changed_count += 1

        for other_segment in all_segments:
            if other_segment.pk == segment.pk and other_segment.__class__ == segment.__class__:
                continue
            other_segment.start_index = _shift_index(other_segment.start_index, original_end, delta)
            other_segment.end_index = _shift_index(other_segment.end_index, original_end, delta)

        for note in call_notes:
            note.start_index = _shift_index(note.start_index, original_end, delta)
            note.end_index = _shift_index(note.end_index, original_end, delta)

    if not changed_count:
        return 0

    call.transcript_text = transcript_text
    call.save(update_fields=["transcript_text", "updated_at"])

    for segment_model in (Question, Answer, Statement):
        changed_segments = [segment for segment in all_segments if isinstance(segment, segment_model)]
        if changed_segments:
            segment_model.objects.bulk_update(changed_segments, ["text", "start_index", "end_index", "updated_at"])

    if call_notes:
        CallNote.objects.bulk_update(call_notes, ["start_index", "end_index", "updated_at"])

    return changed_count


@csrf_exempt
def ghl_call_webhook(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return _json_error("POST required", 405)

    raw_body = request.body or b""
    ghl_signature = request.headers.get("X-GHL-Signature", "")
    legacy_signature = request.headers.get("X-WH-Signature", "")

    is_valid, verification_mode = verify_webhook_signature(
        raw_body,
        ghl_signature=ghl_signature,
        legacy_signature=legacy_signature,
    )
    if not is_valid:
        return _json_error(f"Invalid signature: {verification_mode}", 401)

    try:
        payload: Dict[str, Any] = json.loads(raw_body.decode("utf-8"))
    except Exception:
        return _json_error("Invalid JSON", 400)

    if not is_call_event(payload):
        return JsonResponse(
            {
                "ok": True,
                "stored": False,
                "ignored": True,
                "reason": "not_a_call_event",
            },
            status=202,
        )

    call, event, created = store_call_event(
        payload,
        signature=ghl_signature or legacy_signature,
    )

    logger.info(
        "Stored GHL call webhook event_type=%s call_sid=%s created=%s verification=%s",
        event.event_type,
        getattr(call, "call_sid", "") or getattr(call, "ghl_call_id", ""),
        created,
        verification_mode,
    )
    return JsonResponse(
        {
            "ok": True,
            "stored": True,
            "call_sid": getattr(call, "call_sid", ""),
            "call_id": getattr(call, "ghl_call_id", ""),
            "created": created,
            "verification": verification_mode,
            "transcription_saved": bool(getattr(call, "transcript_text", "")),
        },
        status=202,
    )


@csrf_exempt
def ghl_transcript_webhook(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return _json_error("POST required", 405)

    try:
        payload: Dict[str, Any] = json.loads((request.body or b"").decode("utf-8"))
    except Exception:
        return _json_error("Invalid JSON", 400)

    call, created = upsert_transcript_from_workflow(payload)
    if not call:
        return _json_error("Transcript text or call identifier missing", 400)

    return JsonResponse(
        {
            "ok": True,
            "stored": True,
            "call_sid": call.call_sid,
            "call_id": call.ghl_call_id,
            "created": created,
            "transcript_saved": True,
        },
        status=202,
    )


@staff_member_required
def ghl_call_review(request: HttpRequest, call_id: int):
    call = get_object_or_404(
        GHLCall.objects.prefetch_related(
            "questions",
            "answers",
            "statements",
            "notes",
        ),
        pk=call_id,
    )
    notes = call.notes.select_related("question", "answer", "statement").order_by("start_index", "created_at")
    review_segments = []
    for question in call.questions.all().prefetch_related("answers").order_by("start_index", "id"):
        review_segments.append(
            {
                "kind": "question",
                "kind_label": "Question",
                "text": question.text,
                "speaker_role": question.get_speaker_role_display(),
                "start_index": question.start_index,
                "end_index": question.end_index,
                "question_text": "",
            }
        )
        for answer in question.answers.all().order_by("start_index", "id"):
            review_segments.append(
                {
                    "kind": "answer",
                    "kind_label": "Answer",
                    "text": answer.text,
                    "speaker_role": answer.get_speaker_role_display(),
                    "start_index": answer.start_index,
                    "end_index": answer.end_index,
                    "question_text": question.text,
                }
            )

    for answer in call.answers.filter(question__isnull=True).order_by("start_index", "id"):
        review_segments.append(
            {
                "kind": "answer",
                "kind_label": "Answer",
                "text": answer.text,
                "speaker_role": answer.get_speaker_role_display(),
                "start_index": answer.start_index,
                "end_index": answer.end_index,
                "question_text": "",
            }
        )

    for statement in call.statements.all().order_by("start_index", "id"):
        review_segments.append(
            {
                "kind": "statement",
                "kind_label": "Statement",
                "text": statement.text,
                "speaker_role": statement.get_speaker_role_display(),
                "start_index": statement.start_index,
                "end_index": statement.end_index,
                "question_text": "",
            }
        )

    review_segments.sort(
        key=lambda item: (
            item["start_index"] if item["start_index"] is not None else 10**9,
            item["end_index"] if item["end_index"] is not None else 10**9,
            item["kind_label"],
        )
    )
    return render(
        request,
        "ghl_calls/review.html",
        {
            "call": call,
            "notes": notes,
            "review_segments": review_segments,
            "edit_options": list(CallNote.EditOption.choices),
            "bulk_edit_url": reverse("ghl_call_bulk_edit"),
        },
    )


@staff_member_required
def ghl_call_bulk_edit(request: HttpRequest):
    kind = _normalize_segment_kind(request.GET.get("kind") or request.POST.get("kind") or "question")

    if request.method == "POST":
        search_value = (request.POST.get("q") or "").strip()
        page_number = request.POST.get("page") or "1"
        segment_ids = [segment_id for segment_id in request.POST.getlist("segment_ids") if segment_id.strip()]
        form_state = {
            "find_text": request.POST.get("find_text") or "",
            "replacement_text": request.POST.get("replacement_text") or "",
        }

        if not segment_ids:
            return render(
                request,
                "ghl_calls/bulk_edit.html",
                _bulk_editor_context(
                    request,
                    kind=kind,
                    search_value=search_value,
                    page_number=page_number,
                    form_state=form_state,
                    error_message="Select at least one segment to update.",
                ),
            )

        find_text = form_state["find_text"]
        replacement_text = form_state["replacement_text"]
        if not find_text:
            return render(
                request,
                "ghl_calls/bulk_edit.html",
                _bulk_editor_context(
                    request,
                    kind=kind,
                    search_value=search_value,
                    page_number=page_number,
                    form_state=form_state,
                    error_message="Enter the old word or phrase to replace.",
                ),
            )

        config = SEGMENT_KIND_CONFIG[kind]
        queryset = config["model"].objects.filter(id__in=segment_ids).select_related(*config["select_related"])
        segments = list(queryset)
        if not segments:
            return render(
                request,
                "ghl_calls/bulk_edit.html",
                _bulk_editor_context(
                    request,
                    kind=kind,
                    search_value=search_value,
                    page_number=page_number,
                    form_state=form_state,
                    error_message="The selected segments are no longer available.",
                ),
            )
        with transaction.atomic():
            changed_count = 0
            segments_by_call: dict[int, list[Question | Answer | Statement]] = {}
            for segment in segments:
                segments_by_call.setdefault(segment.call_id, []).append(segment)

            calls = {
                call.id: call
                for call in GHLCall.objects.prefetch_related("questions", "answers", "statements", "notes").filter(
                    id__in=segments_by_call.keys()
                )
            }
            for call_id, selected_segments in segments_by_call.items():
                call = calls.get(call_id)
                if not call:
                    continue
                changed_count += _replace_segment_text_for_call(
                    call=call,
                    selected_segments=selected_segments,
                    find_text=find_text,
                    replacement_text=replacement_text,
                )

        if not changed_count:
            return render(
                request,
                "ghl_calls/bulk_edit.html",
                _bulk_editor_context(
                    request,
                    kind=kind,
                    search_value=search_value,
                    page_number=page_number,
                    form_state=form_state,
                    error_message="None of the selected segments contained that text.",
                ),
            )

        redirect_query = urlencode(
            {
                "kind": kind,
                "q": search_value,
                "page": page_number,
                "updated": changed_count,
            }
        )
        return HttpResponseRedirect(f"{reverse('ghl_call_bulk_edit')}?{redirect_query}")

    search_value = (request.GET.get("q") or "").strip()
    page_number = request.GET.get("page") or "1"
    return render(
        request,
        "ghl_calls/bulk_edit.html",
        _bulk_editor_context(
            request,
            kind=kind,
            search_value=search_value,
            page_number=page_number,
        ),
    )


@staff_member_required
def ghl_question_grouping_review(request: HttpRequest):
    search_value = (request.POST.get("q") or request.GET.get("q") or "").strip()
    show_mode = (request.POST.get("show") or request.GET.get("show") or "ungrouped").strip().lower()
    if show_mode not in {"all", "ungrouped"}:
        show_mode = "ungrouped"
    page_number = request.POST.get("page") or request.GET.get("page") or "1"

    if request.method == "POST":
        action = (request.POST.get("action") or "").strip()
        if action == "auto_group_matches":
            queryset = _question_grouping_queryset(search_value, show_mode).filter(unified_question__isnull=True)
            grouped_count = auto_group_questions(queryset)
            if grouped_count:
                messages.success(request, f"Auto-grouped {grouped_count} question(s).")
            else:
                messages.warning(request, "No high-confidence matches were found to auto-group.")

            redirect_query = urlencode({"q": search_value, "show": show_mode, "page": page_number})
            return HttpResponseRedirect(f"{reverse('ghl_question_grouping_review')}?{redirect_query}")

        question = get_object_or_404(
            Question.objects.select_related("unified_question", "call"),
            pk=request.POST.get("question_id"),
        )
        selected_node = None

        if action == "assign_existing":
            selected_node_id = (request.POST.get("unified_question_id") or "").strip()
            if selected_node_id.isdigit():
                selected_node = UnifiedNodeQuestion.objects.filter(pk=int(selected_node_id)).first()
        elif action == "assign_manual":
            manual_name = (request.POST.get("manual_name") or "").strip()
            if manual_name:
                selected_node = (
                    UnifiedNodeQuestion.objects.filter(name__iexact=manual_name).first()
                    or UnifiedNodeQuestionAlias.objects.select_related("unified_question").filter(name__iexact=manual_name).first()
                )
                if isinstance(selected_node, UnifiedNodeQuestionAlias):
                    selected_node = selected_node.unified_question
        elif action == "create_new":
            new_name = (request.POST.get("new_name") or "").strip() or question.text
            selected_node = UnifiedNodeQuestion.objects.filter(name__iexact=new_name).first()
            if not selected_node:
                selected_node = UnifiedNodeQuestion.objects.create(name=new_name)

        if not selected_node:
            messages.error(request, "Choose a valid unified question to assign.")
        else:
            question.unified_question = selected_node
            question.save(update_fields=["unified_question", "updated_at"])
            alias = ensure_unified_question_alias(selected_node, question.text)
            if alias:
                messages.success(
                    request,
                    f'Linked "{question.text[:80]}" to "{selected_node.name}" and saved "{alias.name}" as an alias.',
                )
            else:
                messages.success(request, f'Linked "{question.text[:80]}" to "{selected_node.name}".')

        redirect_query = urlencode({"q": search_value, "show": show_mode, "page": page_number})
        return HttpResponseRedirect(f"{reverse('ghl_question_grouping_review')}?{redirect_query}")

    return render(
        request,
        "ghl_calls/question_grouping_review.html",
        _question_grouping_context(
            request,
            search_value=search_value,
            show_mode=show_mode,
            page_number=page_number,
        ),
    )


@staff_member_required
@require_POST
def ghl_call_review_create_note(request: HttpRequest, call_id: int) -> JsonResponse:
    call = get_object_or_404(GHLCall, pk=call_id)

    try:
        payload = json.loads((request.body or b"").decode("utf-8"))
    except Exception:
        return _json_error("Invalid JSON", 400)

    try:
        start_index = int(payload.get("start_index"))
        end_index = int(payload.get("end_index"))
    except (TypeError, ValueError):
        return _json_error("Start and end indexes are required", 400)

    transcript_text = call.transcript_text or ""
    if start_index < 0 or end_index <= start_index or end_index > len(transcript_text):
        return _json_error("Invalid transcript selection indexes", 400)

    edit_option = str(payload.get("edit_option") or "").strip().upper()
    valid_edit_options = {choice[0] for choice in CallNote.EditOption.choices}
    if edit_option not in valid_edit_options:
        return _json_error("Invalid edit option", 400)

    score_value = payload.get("negative_impact_score")
    negative_impact_score = None
    if score_value not in (None, ""):
        try:
            negative_impact_score = int(score_value)
        except (TypeError, ValueError):
            return _json_error("Score must be a whole number", 400)

    original_text = str(payload.get("original_text") or transcript_text[start_index:end_index]).strip()
    replacement_text = str(payload.get("replacement_text") or "").strip()
    note_text = str(payload.get("note") or "").strip()

    segment_type, segment = find_best_segment_for_span(call, start_index, end_index)
    note = CallNote.objects.create(
        call=call,
        start_index=start_index,
        end_index=end_index,
        edit_option=edit_option,
        negative_impact_score=negative_impact_score,
        original_text=original_text,
        replacement_text=replacement_text,
        note=note_text,
        question=segment if segment_type == "question" else None,
        answer=segment if segment_type == "answer" else None,
        statement=segment if segment_type == "statement" else None,
    )

    return JsonResponse(
        {
            "ok": True,
            "note_id": note.id,
            "original_text": note.original_text,
            "replacement_text": note.replacement_text,
            "start_index": note.start_index,
            "end_index": note.end_index,
            "edit_option": note.edit_option,
            "negative_impact_score": note.negative_impact_score,
            "segment_type": segment_type or "",
            "segment_id": getattr(segment, "id", None),
        },
        status=201,
    )
