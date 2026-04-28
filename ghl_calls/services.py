from __future__ import annotations

import base64
import difflib
import re
from typing import Any, Dict, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from contacts.models import Contact

from .models import (
    Answer,
    CallNote,
    GHLCall,
    GHLCallWebhookEvent,
    PromptSpec,
    Question,
    Statement,
    UnifiedNodeAnswer,
    UnifiedNodeAnswerAlias,
    UnifiedNodeQuestion,
    UnifiedNodeQuestionAlias,
    UnifiedNodeStatement,
    UnifiedNodeStatementAlias,
)


DEFAULT_SEGMENTATION_PROMPT = (
    "Break the call transcript into ordered segments. Classify each segment as exactly one of: "
    "question, answer, or statement. Keep speaker attribution when available. If a sentence is a "
    "question, it becomes a question. The direct response to the most recent unresolved question "
    "becomes an answer. Everything else becomes a statement. Preserve the original wording. "
    "For unified nodes, group semantically equivalent questions together even when phrased "
    "differently, and do the same for answers and statements. Reuse the same unified node when "
    "the meaning matches. If two segments are materially different in meaning, they must not be "
    "placed in the same unified node."
)

DEFAULT_PROMPT_SPEC_NAME = "Default call segmentation prompt"


def _parse_datetime(value: Any):
    if not value or not isinstance(value, str):
        return None

    dt = parse_datetime(value.replace("Z", "+00:00"))
    if not dt:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _first_attachment(payload: Dict[str, Any]) -> str:
    attachments = payload.get("attachments")
    if isinstance(attachments, list) and attachments:
        first = attachments[0]
        if isinstance(first, str):
            return first.strip()
    return ""


def _extract_transcript_text(payload: Dict[str, Any]) -> str:
    candidates = (
        payload.get("transcript"),
        payload.get("transcriptText"),
        payload.get("transcription"),
        payload.get("transcriptionText"),
        payload.get("callTranscript"),
        payload.get("call_transcript"),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


def _extract_call_sid(payload: Dict[str, Any]) -> str:
    candidates = (
        payload.get("callSid"),
        payload.get("call_sid"),
        payload.get("callSID"),
        payload.get("sid"),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


def _extract_recording_duration(payload: Dict[str, Any]) -> Optional[int]:
    candidates = (
        payload.get("recording_duration"),
        payload.get("recordingDuration"),
        payload.get("call_duration"),
        payload.get("callDuration"),
        payload.get("duration"),
    )
    for candidate in candidates:
        if candidate in (None, ""):
            continue
        try:
            return int(candidate)
        except (TypeError, ValueError):
            continue
    return None


def _extract_started_at(payload: Dict[str, Any]):
    candidates = (
        payload.get("started_at"),
        payload.get("startedAt"),
        payload.get("call_start_time"),
        payload.get("callStartTime"),
        payload.get("start_time"),
        payload.get("startTime"),
        payload.get("dateAdded"),
    )
    for candidate in candidates:
        parsed = _parse_datetime(candidate)
        if parsed:
            return parsed
    return None


def _extract_ended_at(payload: Dict[str, Any]):
    candidates = (
        payload.get("ended_at"),
        payload.get("endedAt"),
        payload.get("call_end_time"),
        payload.get("callEndTime"),
        payload.get("end_time"),
        payload.get("endTime"),
    )
    for candidate in candidates:
        parsed = _parse_datetime(candidate)
        if parsed:
            return parsed
    return None


def _extract_started_at_raw(payload: Dict[str, Any]) -> str:
    candidates = (
        payload.get("started_at"),
        payload.get("startedAt"),
        payload.get("call_start_time"),
        payload.get("callStartTime"),
        payload.get("start_time"),
        payload.get("startTime"),
        payload.get("dateAdded"),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


def _extract_ended_at_raw(payload: Dict[str, Any]) -> str:
    candidates = (
        payload.get("ended_at"),
        payload.get("endedAt"),
        payload.get("call_end_time"),
        payload.get("callEndTime"),
        payload.get("end_time"),
        payload.get("endTime"),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


def _find_existing_call(*, call_sid: str = "", legacy_call_id: str = "", contact_id: str = "", location_id: str = ""):
    matched_by = ""
    call = None

    if call_sid:
        call = GHLCall.objects.filter(call_sid=call_sid).first()
        if call:
            matched_by = "call_sid"
            return call, matched_by

    if legacy_call_id:
        call = GHLCall.objects.filter(ghl_call_id=legacy_call_id).first()
        if call:
            matched_by = "legacy_call_id"
            if call_sid and not call.call_sid:
                call.call_sid = call_sid
                call.save(update_fields=["call_sid", "updated_at"])
            return call, matched_by

    if contact_id:
        call = (
            GHLCall.objects.filter(
                ghl_contact_id=contact_id,
                ghl_location_id=location_id or None,
            )
            .order_by("-created_at")
            .first()
        )
        if call:
            matched_by = "contact_location_fallback"
            return call, matched_by

    return None, matched_by


def _get_segmentation_prompt(call: GHLCall) -> tuple[str, str, Optional[int]]:
    prompt_spec = getattr(call, "prompt_spec", None)
    if prompt_spec and prompt_spec.prompt.strip():
        return (prompt_spec.prompt.strip(), "prompt_spec", prompt_spec.id)
    prompt_spec = _get_or_create_active_prompt_spec()
    if prompt_spec and prompt_spec.prompt.strip():
        return (prompt_spec.prompt.strip(), "active_prompt_spec", prompt_spec.id)
    return (DEFAULT_SEGMENTATION_PROMPT, "default", None)


def _get_or_create_active_prompt_spec() -> PromptSpec:
    prompt_spec = PromptSpec.objects.filter(is_active=True).order_by("-updated_at", "-id").first()
    if prompt_spec:
        return prompt_spec

    prompt_spec = PromptSpec.objects.order_by("-updated_at", "-id").first()
    if prompt_spec:
        if not prompt_spec.is_active:
            prompt_spec.is_active = True
            prompt_spec.save(update_fields=["is_active", "updated_at"])
        return prompt_spec

    return PromptSpec.objects.create(
        name=DEFAULT_PROMPT_SPEC_NAME,
        prompt=DEFAULT_SEGMENTATION_PROMPT,
        is_active=True,
    )


QUESTION_STARTERS = (
    "who",
    "what",
    "when",
    "where",
    "why",
    "how",
    "is",
    "are",
    "am",
    "do",
    "does",
    "did",
    "can",
    "could",
    "would",
    "will",
    "should",
    "have",
    "has",
    "had",
)


SPEAKER_PREFIX_RE = re.compile(
    r"(agent|employee|staff|rep|representative|customer|caller|lead|prospect|contact|speaker 1|speaker 2)\s*[:\-]\s*",
    flags=re.IGNORECASE,
)

TIMECODE_PREFIX_RE = re.compile(r"^\s*(?:(?:\d{1,2}:)?\d{1,2}:\d{2})\s+")
GROUPING_TOKEN_RE = re.compile(r"[a-z0-9]+")
GROUPING_FILLER_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "had",
    "has",
    "have",
    "hello",
    "hey",
    "how",
    "hi",
    "i",
    "is",
    "just",
    "like",
    "me",
    "please",
    "should",
    "thanks",
    "thank",
    "the",
    "to",
    "uh",
    "um",
    "what",
    "when",
    "where",
    "who",
    "why",
    "will",
    "would",
    "you",
}
GROUPING_SYNONYMS = {
    "compensate": "pay",
    "compensated": "pay",
    "compensation": "pay",
    "openings": "hire",
    "opening": "hire",
    "hiring": "hire",
    "hire": "hire",
    "hires": "hire",
    "job": "hire",
    "jobs": "hire",
    "paid": "pay",
    "paying": "pay",
    "position": "hire",
    "positions": "hire",
}
QUESTION_AUTO_GROUP_MIN_SCORE = 72
QUESTION_AUTO_GROUP_MIN_GAP = 8


def _other_speaker(speaker_role: str) -> str:
    if speaker_role == GHLCall.SpeakerRole.EMPLOYEE:
        return GHLCall.SpeakerRole.CUSTOMER
    if speaker_role == GHLCall.SpeakerRole.CUSTOMER:
        return GHLCall.SpeakerRole.EMPLOYEE
    return GHLCall.SpeakerRole.UNKNOWN


def _infer_initiated_by(direction: str) -> str:
    normalized = (direction or "").strip().lower()
    if normalized == GHLCall.Direction.OUTBOUND:
        return GHLCall.SpeakerRole.EMPLOYEE
    if normalized == GHLCall.Direction.INBOUND:
        return GHLCall.SpeakerRole.CUSTOMER
    return GHLCall.SpeakerRole.UNKNOWN


def _normalize_speaker_label(label: str, initiated_by: str) -> str:
    normalized = (label or "").strip().lower()
    if normalized in {"agent", "employee", "staff", "rep", "representative"}:
        return GHLCall.SpeakerRole.EMPLOYEE
    if normalized in {"customer", "caller", "lead", "prospect", "contact"}:
        return GHLCall.SpeakerRole.CUSTOMER
    if normalized == "speaker 1":
        return initiated_by or GHLCall.SpeakerRole.UNKNOWN
    if normalized == "speaker 2":
        return _other_speaker(initiated_by)
    return GHLCall.SpeakerRole.UNKNOWN


def _strip_timecode(text: str) -> tuple[str, int]:
    match = TIMECODE_PREFIX_RE.match(text or "")
    if not match:
        return (text or ""), 0
    return text[match.end() :], match.end()


def _normalize_unified_node_name(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").strip())
    normalized = normalized.rstrip(" .?!,:;")
    return normalized or (text or "").strip()


def _find_unified_node_by_name_or_alias(
    *,
    node_model,
    alias_model,
    alias_fk: str,
    text: str,
):
    name = _normalize_unified_node_name(text)
    if not name:
        return None

    existing = node_model.objects.filter(name__iexact=name).first()
    if existing:
        return existing

    alias = alias_model.objects.select_related(alias_fk).filter(name__iexact=name).first()
    if alias:
        return getattr(alias, alias_fk)
    return None


def _get_or_create_unified_question(text: str) -> UnifiedNodeQuestion | None:
    name = _normalize_unified_node_name(text)
    if not name:
        return None
    existing = _find_unified_node_by_name_or_alias(
        node_model=UnifiedNodeQuestion,
        alias_model=UnifiedNodeQuestionAlias,
        alias_fk="unified_question",
        text=name,
    )
    if existing:
        return existing
    auto_match = _find_auto_unified_question_match(name)
    if auto_match:
        ensure_unified_question_alias(auto_match, name)
        return auto_match
    return UnifiedNodeQuestion.objects.create(name=name)


def _get_or_create_unified_answer(text: str) -> UnifiedNodeAnswer | None:
    name = _normalize_unified_node_name(text)
    if not name:
        return None
    existing = _find_unified_node_by_name_or_alias(
        node_model=UnifiedNodeAnswer,
        alias_model=UnifiedNodeAnswerAlias,
        alias_fk="unified_answer",
        text=name,
    )
    if existing:
        return existing
    return UnifiedNodeAnswer.objects.create(name=name)


def _get_or_create_unified_statement(text: str) -> UnifiedNodeStatement | None:
    name = _normalize_unified_node_name(text)
    if not name:
        return None
    existing = _find_unified_node_by_name_or_alias(
        node_model=UnifiedNodeStatement,
        alias_model=UnifiedNodeStatementAlias,
        alias_fk="unified_statement",
        text=name,
    )
    if existing:
        return existing
    return UnifiedNodeStatement.objects.create(name=name)


def ensure_unified_question_alias(node: UnifiedNodeQuestion, text: str) -> UnifiedNodeQuestionAlias | None:
    name = _normalize_unified_node_name(text)
    if not node or not name:
        return None
    if node.name.strip().lower() == name.lower():
        return None

    existing = UnifiedNodeQuestionAlias.objects.filter(name__iexact=name).first()
    if existing:
        if existing.unified_question_id == node.id:
            return existing
        return None
    return UnifiedNodeQuestionAlias.objects.create(unified_question=node, name=name)


def _normalize_grouping_token(token: str) -> str:
    normalized = (token or "").strip().lower()
    if not normalized:
        return ""

    normalized = GROUPING_SYNONYMS.get(normalized, normalized)

    for suffix in ("ing", "ers", "er", "ed", "es", "s"):
        if len(normalized) > len(suffix) + 2 and normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break

    normalized = GROUPING_SYNONYMS.get(normalized, normalized)
    return normalized


def _grouping_token_list(text: str) -> list[str]:
    normalized = _normalize_unified_node_name(text).lower()
    tokens: list[str] = []
    for raw_token in GROUPING_TOKEN_RE.findall(normalized):
        token = _normalize_grouping_token(raw_token)
        if not token or token in GROUPING_FILLER_WORDS:
            continue
        tokens.append(token)
    return tokens


def _grouping_tokens(text: str) -> set[str]:
    return set(_grouping_token_list(text))


def _question_similarity_score(source_text: str, candidate_text: str) -> int:
    normalized_source = _normalize_unified_node_name(source_text).lower()
    normalized_candidate = _normalize_unified_node_name(candidate_text).lower()
    if not normalized_source or not normalized_candidate:
        return 0
    if normalized_source == normalized_candidate:
        return 100

    source_token_list = _grouping_token_list(normalized_source)
    candidate_token_list = _grouping_token_list(normalized_candidate)
    source_tokens = set(source_token_list)
    candidate_tokens = set(candidate_token_list)
    token_score = 0.0
    if source_tokens and candidate_tokens:
        overlap = len(source_tokens & candidate_tokens)
        union = len(source_tokens | candidate_tokens)
        token_score = overlap / union if union else 0.0

    token_sequence_score = difflib.SequenceMatcher(
        None,
        " ".join(source_token_list),
        " ".join(candidate_token_list),
    ).ratio()
    sequence_score = difflib.SequenceMatcher(None, normalized_source, normalized_candidate).ratio()
    return int(round((token_score * 0.5 + token_sequence_score * 0.3 + sequence_score * 0.2) * 100))


def suggest_unified_questions(question_text: str, *, limit: int = 5, min_score: int = 35) -> list[dict[str, Any]]:
    normalized_question = _normalize_unified_node_name(question_text)
    if not normalized_question:
        return []

    suggestions: list[dict[str, Any]] = []
    for node in UnifiedNodeQuestion.objects.prefetch_related("aliases").all():
        best_score = _question_similarity_score(normalized_question, node.name)
        best_match = node.name
        match_source = "canonical"

        for alias in node.aliases.all():
            alias_score = _question_similarity_score(normalized_question, alias.name)
            if alias_score > best_score:
                best_score = alias_score
                best_match = alias.name
                match_source = "alias"

        if best_score < min_score:
            continue

        suggestions.append(
            {
                "node": node,
                "score": best_score,
                "matched_text": best_match,
                "match_source": match_source,
            }
        )

    suggestions.sort(key=lambda item: (-item["score"], item["node"].name.lower()))
    return suggestions[:limit]


def _find_auto_unified_question_match(text: str) -> UnifiedNodeQuestion | None:
    suggestions = suggest_unified_questions(text, limit=2, min_score=QUESTION_AUTO_GROUP_MIN_SCORE)
    if not suggestions:
        return None

    top_match = suggestions[0]
    second_score = suggestions[1]["score"] if len(suggestions) > 1 else 0
    if second_score and (top_match["score"] - second_score) < QUESTION_AUTO_GROUP_MIN_GAP:
        return None
    return top_match["node"]


def assign_unified_question(question: Question) -> UnifiedNodeQuestion | None:
    if not question or not (question.text or "").strip():
        return None

    node = _get_or_create_unified_question(question.text)
    if not node:
        return None

    changed_fields = []
    if question.unified_question_id != node.id:
        question.unified_question = node
        changed_fields.append("unified_question")
    if changed_fields:
        changed_fields.append("updated_at")
        question.save(update_fields=changed_fields)

    ensure_unified_question_alias(node, question.text)
    return node


def auto_group_questions(queryset) -> int:
    grouped_count = 0
    for question in queryset:
        if assign_unified_question(question):
            grouped_count += 1
    return grouped_count


def _split_transcript_segments(transcript_text: str, initiated_by: str) -> list[tuple[int, int, str, str]]:
    segments: list[tuple[int, int, str, str]] = []

    current_speaker = GHLCall.SpeakerRole.UNKNOWN

    for match in re.finditer(r"[^\n]+", transcript_text, flags=re.MULTILINE):
        raw_line = match.group(0)
        stripped_line = raw_line.strip()
        if not stripped_line:
            continue

        line_start = transcript_text.find(stripped_line, match.start())
        line_start = line_start if line_start >= 0 else match.start()

        line_text, timecode_prefix_len = _strip_timecode(stripped_line)
        line_text = line_text.strip()
        if not line_text:
            continue

        speaker_matches = list(SPEAKER_PREFIX_RE.finditer(line_text))
        if speaker_matches:
            for index, speaker_match in enumerate(speaker_matches):
                speaker_role = _normalize_speaker_label(speaker_match.group(1), initiated_by)
                current_speaker = speaker_role
                block_start = speaker_match.end()
                block_end = (
                    speaker_matches[index + 1].start()
                    if index + 1 < len(speaker_matches)
                    else len(line_text)
                )
                block_text = line_text[block_start:block_end].strip()
                if not block_text:
                    continue

                block_offset = line_text.find(block_text, block_start)
                block_offset = block_offset if block_offset >= 0 else block_start

                for sentence in re.finditer(r"[^.!?\n]+[.!?]?", block_text):
                    text = sentence.group(0).strip()
                    if text:
                        start_index = line_start + timecode_prefix_len + block_offset + sentence.start()
                        end_index = line_start + timecode_prefix_len + block_offset + sentence.end()
                        segments.append((start_index, end_index, text, speaker_role))
            continue

        speaker_role = current_speaker
        content_start = line_start + timecode_prefix_len
        if not raw_line:
            continue

        for sentence in re.finditer(r"[^.!?\n]+[.!?]?", line_text):
            text = sentence.group(0).strip()
            if text:
                start_index = content_start + sentence.start()
                end_index = content_start + sentence.end()
                segments.append((start_index, end_index, text, speaker_role))
    return segments


def _looks_like_question(text: str) -> bool:
    normalized = text.strip().lower()
    if not normalized:
        return False
    if normalized.endswith("?"):
        return True
    return normalized.startswith(QUESTION_STARTERS)


def _call_has_manual_segment_data(call: GHLCall) -> bool:
    if call.notes.exists():
        return True

    segment_groups = (call.questions.all(), call.answers.all(), call.statements.all())
    for queryset in segment_groups:
        for segment in queryset:
            if segment.ai_accuracy_score is not None or segment.human_accuracy_score is not None:
                return True
    return False


def _segment_span(segment: Question | Answer | Statement) -> tuple[int, int]:
    start_index = segment.start_index if segment.start_index is not None else -1
    end_index = segment.end_index if segment.end_index is not None else -1
    return start_index, end_index


def find_best_segment_for_span(call: GHLCall, start_index: int, end_index: int) -> tuple[str, Question | Answer | Statement | None]:
    candidates: list[tuple[int, str, Question | Answer | Statement]] = []
    segment_groups = (
        ("question", call.questions.all()),
        ("answer", call.answers.all()),
        ("statement", call.statements.all()),
    )

    for segment_type, queryset in segment_groups:
        for segment in queryset:
            segment_start, segment_end = _segment_span(segment)
            if segment_start < 0 or segment_end < 0:
                continue
            if segment_start <= start_index and end_index <= segment_end:
                span_size = segment_end - segment_start
                candidates.append((span_size, segment_type, segment))

    if not candidates:
        return ("", None)

    candidates.sort(key=lambda item: item[0])
    _, segment_type, segment = candidates[0]
    return (segment_type, segment)


def sync_call_segments_from_transcript(call: GHLCall) -> int:
    transcript_text = (call.transcript_text or "").strip()
    if not transcript_text:
        return 0

    if _call_has_manual_segment_data(call):
        return 0

    segmentation_prompt, prompt_source, prompt_spec_id = _get_segmentation_prompt(call)
    initiated_by = call.initiated_by or GHLCall.SpeakerRole.UNKNOWN
    segments = _split_transcript_segments(transcript_text, initiated_by)
    if not segments:
        return 0

    with transaction.atomic():
        call.questions.all().delete()
        call.answers.all().delete()
        call.statements.all().delete()

        created_count = 0
        current_question: Question | None = None
        question_speaker = GHLCall.SpeakerRole.UNKNOWN
        answer_speaker = GHLCall.SpeakerRole.UNKNOWN
        answer_mode = False

        for start_index, end_index, text, explicit_speaker in segments:
            segment_speaker = explicit_speaker or GHLCall.SpeakerRole.UNKNOWN
            common_fields = {
                "call": call,
                "speaker_role": segment_speaker,
                "text": text,
                "start_index": start_index,
                "end_index": end_index,
            }
            if _looks_like_question(text):
                common_fields["unified_question"] = _get_or_create_unified_question(text)
                current_question = Question.objects.create(**common_fields)
                question_speaker = segment_speaker
                answer_speaker = (
                    _other_speaker(segment_speaker)
                    if segment_speaker != GHLCall.SpeakerRole.UNKNOWN
                    else GHLCall.SpeakerRole.UNKNOWN
                )
                answer_mode = True
            elif answer_mode:
                if (
                    segment_speaker != GHLCall.SpeakerRole.UNKNOWN
                    and segment_speaker == question_speaker
                ):
                    Statement.objects.create(**common_fields)
                    answer_mode = False
                    answer_speaker = GHLCall.SpeakerRole.UNKNOWN
                    question_speaker = GHLCall.SpeakerRole.UNKNOWN
                    current_question = None
                else:
                    if segment_speaker == GHLCall.SpeakerRole.UNKNOWN:
                        resolved_answer_speaker = (
                            answer_speaker
                            if answer_speaker != GHLCall.SpeakerRole.UNKNOWN
                            else _other_speaker(question_speaker)
                        )
                    else:
                        resolved_answer_speaker = segment_speaker
                    common_fields["speaker_role"] = resolved_answer_speaker
                    common_fields["unified_answer"] = _get_or_create_unified_answer(text)
                    common_fields["question"] = current_question
                    Answer.objects.create(**common_fields)
                    answer_speaker = resolved_answer_speaker
                    answer_mode = resolved_answer_speaker != GHLCall.SpeakerRole.UNKNOWN
            else:
                common_fields["unified_statement"] = _get_or_create_unified_statement(text)
                Statement.objects.create(**common_fields)
                question_speaker = segment_speaker
                answer_speaker = GHLCall.SpeakerRole.UNKNOWN
                answer_mode = False
                current_question = None
            created_count += 1

        raw_transcription_response = dict(call.raw_transcription_response or {})
        raw_transcription_response["segmentation"] = {
            "prompt": segmentation_prompt,
            "prompt_source": prompt_source,
            "prompt_spec_id": prompt_spec_id,
            "strategy": "heuristic_fallback",
            "segment_count": created_count,
        }
        call.raw_transcription_response = raw_transcription_response
        update_fields = ["raw_transcription_response", "updated_at"]
        if prompt_spec_id and not call.prompt_spec_id:
            call.prompt_spec_id = prompt_spec_id
            update_fields.append("prompt_spec")
        call.save(update_fields=update_fields)

    return created_count


def upsert_transcript_from_workflow(payload: Dict[str, Any]) -> tuple[Optional[GHLCall], bool]:
    call_sid = _extract_call_sid(payload)
    legacy_call_id = str(
        payload.get("messageId")
        or payload.get("callId")
        or payload.get("message_id")
        or payload.get("call_id")
        or ""
    ).strip()
    contact_id = str(payload.get("contactId") or payload.get("contact_id") or "").strip()
    location_id = str(payload.get("locationId") or payload.get("location_id") or "").strip()
    transcript_text = _extract_transcript_text(payload)

    if not transcript_text:
        return None, False

    call = None
    created = False
    call, _matched_by = _find_existing_call(
        call_sid=call_sid,
        legacy_call_id=legacy_call_id,
        contact_id=contact_id,
        location_id=location_id,
    )

    existing_recording_url = getattr(call, "recording_url", "") if call else ""
    existing_started_at = getattr(call, "started_at", None) if call else None
    existing_raw_started_at = getattr(call, "raw_started_at", "") if call else ""
    existing_ended_at = getattr(call, "ended_at", None) if call else None
    existing_raw_ended_at = getattr(call, "raw_ended_at", "") if call else ""
    existing_recording_duration = getattr(call, "recording_duration_seconds", None) if call else None

    defaults = {
        "call_sid": call_sid,
        "ghl_contact_id": contact_id,
        "ghl_location_id": location_id,
        "contact": _match_contact(contact_id),
        "direction": str(payload.get("direction") or "unknown").strip().lower() or "unknown",
        "initiated_by": str(payload.get("initiatedBy") or payload.get("initiated_by") or "").strip().lower()
        or _infer_initiated_by(str(payload.get("direction") or "")),
        "status": str(payload.get("status") or payload.get("callStatus") or "").strip(),
        "from_number": str(payload.get("from") or payload.get("from_number") or "").strip(),
        "to_number": str(payload.get("to") or payload.get("to_number") or "").strip(),
        "recording_url": str(payload.get("recordingUrl") or payload.get("recording_url") or "").strip() or existing_recording_url,
        "recording_duration_seconds": _extract_recording_duration(payload) or existing_recording_duration,
        "started_at": _extract_started_at(payload) or existing_started_at,
        "raw_started_at": _extract_started_at_raw(payload) or existing_raw_started_at,
        "ended_at": _extract_ended_at(payload) or existing_ended_at,
        "raw_ended_at": _extract_ended_at_raw(payload) or existing_raw_ended_at,
        "transcript_text": transcript_text,
        "transcription_model": "gohighlevel",
        "processing_status": GHLCall.ProcessingStatus.TRANSCRIBED,
        "transcription_error": "",
        "raw_transcription_response": payload,
        "last_webhook_received_at": timezone.now(),
    }

    if call:
        for field, value in defaults.items():
            setattr(call, field, value)
        if not call.ghl_call_id and legacy_call_id:
            call.ghl_call_id = legacy_call_id
        call.save()
        sync_call_segments_from_transcript(call)
        return call, False

    fallback_key = call_sid or legacy_call_id
    if not fallback_key:
        return None, False

    defaults["raw_payload"] = payload
    defaults["raw_recording_metadata"] = {}
    defaults["ghl_call_id"] = legacy_call_id or call_sid
    lookup = {"call_sid": call_sid} if call_sid else {"ghl_call_id": legacy_call_id}
    call, created = GHLCall.objects.update_or_create(
        **lookup,
        defaults=defaults,
    )
    sync_call_segments_from_transcript(call)
    return call, created


def is_call_event(payload: Dict[str, Any]) -> bool:
    message_type = str(payload.get("messageType") or "").strip().upper()
    type_name = str(payload.get("type") or "").strip()
    return bool(
        type_name == "OutboundMessage"
        and (
            message_type == "CALL"
            or "callDuration" in payload
            or "callStatus" in payload
        )
    )


def normalize_call_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize raw GHL webhook payloads into a predictable dict shape.

    Runtime ingestion/transcription wiring is intentionally added in a later step.
    """
    call_status = str(payload.get("callStatus") or payload.get("status") or "").strip()

    call_sid = _extract_call_sid(payload)
    return {
        "event_type": str(payload.get("type") or payload.get("eventType") or "").strip(),
        "event_id": str(payload.get("webhookId") or payload.get("id") or payload.get("eventId") or "").strip(),
        "call_id": call_sid,
        "legacy_call_id": str(payload.get("callId") or payload.get("messageId") or "").strip(),
        "contact_id": str(payload.get("contactId") or "").strip(),
        "location_id": str(payload.get("locationId") or "").strip(),
        "direction": str(payload.get("direction") or "unknown").strip().lower() or "unknown",
        "status": call_status,
        "from_number": str(payload.get("from") or "").strip(),
        "to_number": str(payload.get("to") or "").strip(),
        "recording_url": _first_attachment(payload),
        "recording_duration_seconds": payload.get("callDuration"),
        "started_at": _parse_datetime(payload.get("dateAdded")),
        "raw_started_at": str(payload.get("dateAdded") or "").strip(),
        "raw_ended_at": "",
        "payload": payload,
    }


def _load_public_key(public_key_pem: str):
    public_key_pem = (public_key_pem or "").replace("\\n", "\n").strip()
    return serialization.load_pem_public_key(public_key_pem.encode("utf-8"))


def verify_webhook_signature(raw_body: bytes, *, ghl_signature: str = "", legacy_signature: str = "") -> tuple[bool, str]:
    if ghl_signature:
        try:
            public_key = _load_public_key(settings.GHL_WEBHOOK_PUBLIC_KEY)
            if not isinstance(public_key, ed25519.Ed25519PublicKey):
                return False, "Invalid Ed25519 public key configuration"
            public_key.verify(base64.b64decode(ghl_signature), raw_body)
            return True, "verified_ed25519"
        except (ValueError, TypeError, InvalidSignature):
            return False, "invalid_x_ghl_signature"

    if legacy_signature:
        try:
            public_key = _load_public_key(settings.GHL_WEBHOOK_LEGACY_PUBLIC_KEY)
            if not isinstance(public_key, rsa.RSAPublicKey):
                return False, "Invalid RSA public key configuration"
            public_key.verify(
                base64.b64decode(legacy_signature),
                raw_body,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return True, "verified_x_wh_signature"
        except (ValueError, TypeError, InvalidSignature):
            return False, "invalid_x_wh_signature"

    if getattr(settings, "GHL_CALLS_ALLOW_UNSIGNED_WEBHOOKS", False):
        return True, "unsigned_allowed"

    return False, "missing_signature"


def _match_contact(ghl_contact_id: str) -> Optional[Contact]:
    if not ghl_contact_id:
        return None
    return Contact.objects.filter(privser_contact_id=ghl_contact_id).first()


def store_call_event(payload: Dict[str, Any], *, signature: str = "") -> tuple[Optional[GHLCall], GHLCallWebhookEvent, bool]:
    normalized = normalize_call_payload(payload)
    call = None
    created = False
    transcript_text = _extract_transcript_text(payload)
    processing_status = (
        GHLCall.ProcessingStatus.TRANSCRIBED
        if transcript_text
        else GHLCall.ProcessingStatus.PENDING
    )

    effective_call_key = normalized["call_id"] or normalized["legacy_call_id"]
    if effective_call_key:
        existing_call, _matched_by = _find_existing_call(
            call_sid=normalized["call_id"],
            legacy_call_id=normalized["legacy_call_id"],
            contact_id=normalized["contact_id"],
            location_id=normalized["location_id"],
        )

        defaults = {
            "call_sid": normalized["call_id"],
            "ghl_call_id": normalized["legacy_call_id"] or normalized["call_id"],
            "ghl_contact_id": normalized["contact_id"],
            "ghl_location_id": normalized["location_id"],
            "contact": _match_contact(normalized["contact_id"]),
            "direction": normalized["direction"],
            "initiated_by": _infer_initiated_by(normalized["direction"]),
            "status": normalized["status"],
            "from_number": normalized["from_number"],
            "to_number": normalized["to_number"],
            "recording_url": normalized["recording_url"],
            "recording_duration_seconds": normalized["recording_duration_seconds"],
            "started_at": normalized["started_at"],
            "raw_started_at": normalized["raw_started_at"],
            "raw_ended_at": normalized["raw_ended_at"],
            "transcript_text": transcript_text,
            "processing_status": processing_status,
            "transcription_model": "gohighlevel" if transcript_text else "",
            "transcription_error": "",
            "raw_transcription_response": {},
            "raw_payload": normalized["payload"],
            "raw_recording_metadata": {
                "attachments": normalized["payload"].get("attachments", []),
            },
            "last_webhook_received_at": timezone.now(),
        }
        if existing_call:
            for field, value in defaults.items():
                setattr(existing_call, field, value)
            existing_call.save()
            call = existing_call
            created = False
        else:
            lookup = {"call_sid": normalized["call_id"]} if normalized["call_id"] else {
                "ghl_call_id": normalized["legacy_call_id"]
            }
            call, created = GHLCall.objects.update_or_create(
                **lookup,
                defaults=defaults,
            )
        if transcript_text:
            sync_call_segments_from_transcript(call)

    event = GHLCallWebhookEvent.objects.create(
        event_type=normalized["event_type"] or "unknown",
        event_id=normalized["event_id"],
        call=call,
        signature=signature[:255],
        payload=payload,
        processed_at=timezone.now(),
    )
    return call, event, created
