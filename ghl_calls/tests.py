from __future__ import annotations

import json
from unittest.mock import patch

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from companies.models import Company
from contacts.models import Contact

from django.contrib.admin.options import StackedInline

from .admin import AnswerAdmin, CallNoteAdmin, QuestionAdmin, QuestionAnswerInline, StatementAdmin
from .models import (
    Answer,
    CallNote,
    GHLCall,
    GHLCallTranscriptBulkEdit,
    GHLCallWebhookEvent,
    PromptSpec,
    Question,
    QuestionGroupingReview,
    Statement,
    UnifiedNodeAnswer,
    UnifiedNodeQuestion,
    UnifiedNodeQuestionAlias,
    UnifiedNodeStatement,
)
from .services import (
    auto_group_questions,
    ensure_unified_question_alias,
    normalize_call_payload,
    suggest_unified_questions,
    sync_call_segments_from_transcript,
    upsert_transcript_from_workflow,
    verify_webhook_signature,
)


class GHLCallServicesTests(TestCase):
    def test_call_note_can_store_targeted_text_replacement(self):
        company = Company.objects.create(name="Correction Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Rosalind",
            last_name="Franklin",
            email="rosalind@example.com",
            phone="+15550000010",
        )
        call = GHLCall.objects.create(
            ghl_call_id="call_note_1",
            ghl_contact_id="ghl_contact_note_1",
            ghl_location_id="loc_note_1",
            contact=contact,
            transcript_text="Yes, training is paid.",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )
        answer = Answer.objects.create(
            call=call,
            speaker_role=GHLCall.SpeakerRole.EMPLOYEE,
            text="Yes, training is paid.",
            ai_accuracy_score=0,
            human_accuracy_score=0,
            start_index=0,
            end_index=22,
        )

        note = CallNote.objects.create(
            call=call,
            answer=answer,
            start_index=0,
            end_index=3,
            edit_option=CallNote.EditOption.CHANGE,
            negative_impact_score=90,
            original_text="Yes",
            replacement_text="No",
            note="Change the answer from yes to no.",
        )

        self.assertEqual(note.original_text, "Yes")
        self.assertEqual(note.replacement_text, "No")
        self.assertEqual(note.edit_option, CallNote.EditOption.CHANGE)
        self.assertEqual(note.negative_impact_score, 90)

    def test_normalize_call_payload_extracts_core_fields(self):
        payload = {
            "type": "OutboundMessage",
            "id": "evt_1",
            "callSid": "CA123",
            "messageId": "call_123",
            "contactId": "ghl_contact_1",
            "locationId": "loc_1",
            "direction": "outbound",
            "callStatus": "completed",
            "messageType": "CALL",
            "from": "+15550000001",
            "to": "+15550000002",
            "attachments": ["https://example.com/audio.mp3"],
            "callDuration": 42,
            "dateAdded": "2026-03-22T10:30:00Z",
        }

        normalized = normalize_call_payload(payload)

        self.assertEqual(normalized["event_type"], "OutboundMessage")
        self.assertEqual(normalized["event_id"], "evt_1")
        self.assertEqual(normalized["call_id"], "CA123")
        self.assertEqual(normalized["legacy_call_id"], "call_123")
        self.assertEqual(normalized["contact_id"], "ghl_contact_1")
        self.assertEqual(normalized["recording_url"], "https://example.com/audio.mp3")
        self.assertEqual(normalized["recording_duration_seconds"], 42)
        self.assertIsNotNone(normalized["started_at"])
        self.assertEqual(normalized["raw_started_at"], "2026-03-22T10:30:00Z")
        self.assertEqual(normalized["raw_ended_at"], "")

    @override_settings(GHL_CALLS_ALLOW_UNSIGNED_WEBHOOKS=True)
    def test_verify_webhook_signature_allows_unsigned_when_enabled(self):
        is_valid, mode = verify_webhook_signature(b"{}")
        self.assertTrue(is_valid)
        self.assertEqual(mode, "unsigned_allowed")

    def test_upsert_transcript_from_workflow_creates_transcribed_call(self):
        payload = {
            "callSid": "CA_TRANSCRIPT_1",
            "messageId": "call_transcript_1",
            "contactId": "ghl_contact_1",
            "locationId": "loc_1",
            "transcript": "Hello from GHL transcript",
            "direction": "outbound",
            "status": "completed",
        }

        call, created = upsert_transcript_from_workflow(payload)

        self.assertTrue(created)
        self.assertIsNotNone(call)
        self.assertEqual(call.call_sid, "CA_TRANSCRIPT_1")
        self.assertEqual(call.ghl_call_id, "call_transcript_1")
        self.assertEqual(call.transcript_text, "Hello from GHL transcript")
        self.assertEqual(call.processing_status, GHLCall.ProcessingStatus.TRANSCRIBED)

    def test_upsert_transcript_from_workflow_preserves_raw_timestamp_strings(self):
        payload = {
            "callSid": "CA_TRANSCRIPT_2",
            "contactId": "ghl_contact_1",
            "locationId": "loc_1",
            "transcript": "Hello from GHL transcript",
            "startedAt": "2026-03-26T15:00:00Z",
            "endedAt": "2026-03-26T15:02:00Z",
        }

        call, created = upsert_transcript_from_workflow(payload)

        self.assertTrue(created)
        self.assertIsNotNone(call)
        self.assertEqual(call.raw_started_at, "2026-03-26T15:00:00Z")
        self.assertEqual(call.raw_ended_at, "2026-03-26T15:02:00Z")
        self.assertIsNotNone(call.started_at)
        self.assertIsNotNone(call.ended_at)

    def test_sync_call_segments_from_transcript_splits_questions_answers_and_statements(self):
        company = Company.objects.create(name="Segment Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Alan",
            last_name="Turing",
            email="alan@example.com",
            phone="+15550000003",
        )
        call = GHLCall.objects.create(
            ghl_call_id="call_parse_1",
            ghl_contact_id="ghl_contact_parse",
            ghl_location_id="loc_parse",
            contact=contact,
            transcript_text="Hello there. Are you open today? Yes, we are open today. Great.",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )

        created_count = sync_call_segments_from_transcript(call)

        self.assertEqual(created_count, 4)
        self.assertEqual(call.questions.count(), 1)
        self.assertEqual(call.answers.count(), 1)
        self.assertEqual(call.statements.count(), 2)
        self.assertEqual(call.questions.first().text, "Are you open today?")
        self.assertEqual(call.answers.first().text, "Yes, we are open today.")
        self.assertEqual(call.questions.first().speaker_role, GHLCall.SpeakerRole.UNKNOWN)
        self.assertEqual(call.answers.first().speaker_role, GHLCall.SpeakerRole.UNKNOWN)

    def test_sync_call_segments_respects_speaker_labels(self):
        company = Company.objects.create(name="Speaker Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Grace",
            last_name="Hopper",
            email="grace@example.com",
            phone="+15550000004",
        )
        call = GHLCall.objects.create(
            ghl_call_id="call_parse_2",
            ghl_contact_id="ghl_contact_parse_2",
            ghl_location_id="loc_parse_2",
            contact=contact,
            initiated_by=GHLCall.SpeakerRole.EMPLOYEE,
            transcript_text="Agent: Hello there. Customer: Are you open today? Agent: Yes, we are open today.",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )

        created_count = sync_call_segments_from_transcript(call)

        self.assertEqual(created_count, 3)
        self.assertEqual(call.statements.first().speaker_role, GHLCall.SpeakerRole.EMPLOYEE)
        self.assertEqual(call.questions.first().speaker_role, GHLCall.SpeakerRole.CUSTOMER)
        self.assertEqual(call.answers.first().speaker_role, GHLCall.SpeakerRole.EMPLOYEE)
        self.assertEqual(call.answers.first().question_id, call.questions.first().id)

    def test_sync_call_segments_keeps_multi_sentence_labeled_answer_together(self):
        company = Company.objects.create(name="Turn Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Katherine",
            last_name="Johnson",
            email="katherine@example.com",
            phone="+15550000005",
        )
        call = GHLCall.objects.create(
            ghl_call_id="call_parse_3",
            ghl_contact_id="ghl_contact_parse_3",
            ghl_location_id="loc_parse_3",
            contact=contact,
            initiated_by=GHLCall.SpeakerRole.CUSTOMER,
            transcript_text=(
                "Customer: Is training paid? "
                "Agent: Yes, training is paid. It also includes support for 30 days. "
                "Customer: Great."
            ),
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )

        created_count = sync_call_segments_from_transcript(call)

        self.assertEqual(created_count, 4)
        self.assertEqual(call.questions.count(), 1)
        self.assertEqual(call.answers.count(), 2)
        self.assertEqual(call.statements.count(), 1)
        self.assertEqual(
            list(call.answers.values_list("text", flat=True)),
            ["Yes, training is paid.", "It also includes support for 30 days."],
        )
        self.assertTrue(
            all(
                speaker == GHLCall.SpeakerRole.EMPLOYEE
                for speaker in call.answers.values_list("speaker_role", flat=True)
            )
        )
        self.assertTrue(
            all(
                question_id == call.questions.first().id
                for question_id in call.answers.values_list("question_id", flat=True)
            )
        )

    def test_sync_call_segments_strips_timecodes_and_keeps_speaker_context_on_followup_lines(self):
        company = Company.objects.create(name="Timecode Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Mary",
            last_name="Jackson",
            email="mary@example.com",
            phone="+15550000006",
        )
        call = GHLCall.objects.create(
            ghl_call_id="call_parse_4",
            ghl_contact_id="ghl_contact_parse_4",
            ghl_location_id="loc_parse_4",
            contact=contact,
            initiated_by=GHLCall.SpeakerRole.EMPLOYEE,
            transcript_text=(
                "00:01 Agent: Hello there.\n"
                "00:04 Customer: Are you open today?\n"
                "00:06 Agent: Yes, we are open today.\n"
                "00:08 We close at five."
            ),
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )

        created_count = sync_call_segments_from_transcript(call)

        self.assertEqual(created_count, 4)
        self.assertEqual(call.statements.first().text, "Hello there.")
        self.assertEqual(call.questions.first().text, "Are you open today?")
        self.assertEqual(
            list(call.answers.values_list("text", flat=True)),
            ["Yes, we are open today.", "We close at five."],
        )
        self.assertTrue(
            all(
                not text.startswith("00:")
                for text in call.answers.values_list("text", flat=True)
            )
        )
        self.assertTrue(
            all(
                question_id == call.questions.first().id
                for question_id in call.answers.values_list("question_id", flat=True)
            )
        )

    def test_sync_call_segments_creates_unified_nodes(self):
        company = Company.objects.create(name="Unified Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Dorothy",
            last_name="Vaughan",
            email="dorothy@example.com",
            phone="+15550000007",
        )
        call = GHLCall.objects.create(
            ghl_call_id="call_parse_5",
            ghl_contact_id="ghl_contact_parse_5",
            ghl_location_id="loc_parse_5",
            contact=contact,
            initiated_by=GHLCall.SpeakerRole.CUSTOMER,
            transcript_text="Hello there. Is training paid? Yes, training is paid.",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )

        created_count = sync_call_segments_from_transcript(call)

        self.assertEqual(created_count, 3)
        self.assertEqual(UnifiedNodeStatement.objects.count(), 1)
        self.assertEqual(UnifiedNodeQuestion.objects.count(), 1)
        self.assertEqual(UnifiedNodeAnswer.objects.count(), 1)
        self.assertIsNotNone(call.statements.first().unified_statement)
        self.assertIsNotNone(call.questions.first().unified_question)
        self.assertIsNotNone(call.answers.first().unified_answer)

    def test_sync_call_segments_reuses_existing_unified_nodes(self):
        existing_question = UnifiedNodeQuestion.objects.create(name="Is training paid")
        existing_answer = UnifiedNodeAnswer.objects.create(name="Yes, training is paid")
        existing_statement = UnifiedNodeStatement.objects.create(name="Hello there")

        company = Company.objects.create(name="Reuse Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Annie",
            last_name="Easley",
            email="annie@example.com",
            phone="+15550000008",
        )
        call = GHLCall.objects.create(
            ghl_call_id="call_parse_6",
            ghl_contact_id="ghl_contact_parse_6",
            ghl_location_id="loc_parse_6",
            contact=contact,
            initiated_by=GHLCall.SpeakerRole.CUSTOMER,
            transcript_text="Hello there. Is training paid? Yes, training is paid.",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )

        created_count = sync_call_segments_from_transcript(call)

        self.assertEqual(created_count, 3)
        self.assertEqual(UnifiedNodeStatement.objects.count(), 1)
        self.assertEqual(UnifiedNodeQuestion.objects.count(), 1)
        self.assertEqual(UnifiedNodeAnswer.objects.count(), 1)
        self.assertEqual(call.statements.first().unified_statement_id, existing_statement.id)
        self.assertEqual(call.questions.first().unified_question_id, existing_question.id)
        self.assertEqual(call.answers.first().unified_answer_id, existing_answer.id)

    def test_sync_call_segments_reuses_existing_question_node_by_alias(self):
        existing_question = UnifiedNodeQuestion.objects.create(name="Is training paid")
        UnifiedNodeQuestionAlias.objects.create(
            unified_question=existing_question,
            name="Do you pay for training",
        )

        company = Company.objects.create(name="Alias Reuse Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Barbara",
            last_name="McClintock",
            email="barbara@example.com",
            phone="+15550000081",
        )
        call = GHLCall.objects.create(
            ghl_call_id="call_parse_alias_1",
            ghl_contact_id="ghl_contact_parse_alias_1",
            ghl_location_id="loc_parse_alias_1",
            contact=contact,
            initiated_by=GHLCall.SpeakerRole.CUSTOMER,
            transcript_text="Do you pay for training? Yes, we do.",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )

        created_count = sync_call_segments_from_transcript(call)

        self.assertEqual(created_count, 2)
        self.assertEqual(call.questions.count(), 1)
        self.assertEqual(call.questions.first().unified_question_id, existing_question.id)

    def test_sync_call_segments_auto_groups_semantic_question_match(self):
        existing_question = UnifiedNodeQuestion.objects.create(name="Is training paid")

        company = Company.objects.create(name="Semantic Auto Group Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Rosalyn",
            last_name="Yalow",
            email="rosalyn@example.com",
            phone="+15550000082",
        )
        call = GHLCall.objects.create(
            ghl_call_id="call_parse_semantic_1",
            ghl_contact_id="ghl_contact_parse_semantic_1",
            ghl_location_id="loc_parse_semantic_1",
            contact=contact,
            initiated_by=GHLCall.SpeakerRole.CUSTOMER,
            transcript_text="Do you pay for training? Yes, we do.",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )

        created_count = sync_call_segments_from_transcript(call)

        self.assertEqual(created_count, 2)
        self.assertEqual(call.questions.count(), 1)
        self.assertEqual(call.questions.first().unified_question_id, existing_question.id)
        self.assertTrue(
            UnifiedNodeQuestionAlias.objects.filter(
                unified_question=existing_question,
                name="Do you pay for training",
            ).exists()
        )

    def test_sync_call_segments_keeps_different_question_meanings_separate(self):
        existing_question = UnifiedNodeQuestion.objects.create(name="Do you hire contractors")

        company = Company.objects.create(name="Separate Meaning Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Chien",
            last_name="Shiung",
            email="chien@example.com",
            phone="+15550000083",
        )
        call = GHLCall.objects.create(
            ghl_call_id="call_parse_semantic_2",
            ghl_contact_id="ghl_contact_parse_semantic_2",
            ghl_location_id="loc_parse_semantic_2",
            contact=contact,
            initiated_by=GHLCall.SpeakerRole.CUSTOMER,
            transcript_text="Are you hiring full time? Yes, we are.",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )

        created_count = sync_call_segments_from_transcript(call)

        self.assertEqual(created_count, 2)
        self.assertEqual(UnifiedNodeQuestion.objects.count(), 2)
        self.assertNotEqual(call.questions.first().unified_question_id, existing_question.id)

    def test_suggest_unified_questions_considers_aliases(self):
        canonical = UnifiedNodeQuestion.objects.create(name="Is training paid")
        ensure_unified_question_alias(canonical, "Do you pay for training")

        suggestions = suggest_unified_questions("Do you compensate training?")

        self.assertTrue(suggestions)
        self.assertEqual(suggestions[0]["node"].id, canonical.id)
        self.assertIn(suggestions[0]["match_source"], {"canonical", "alias"})
        self.assertGreater(suggestions[0]["score"], 35)

    def test_auto_group_questions_assigns_high_confidence_matches(self):
        canonical = UnifiedNodeQuestion.objects.create(name="Is training paid")
        company = Company.objects.create(name="Bulk Group Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Vera",
            last_name="Rubin",
            email="vera@example.com",
            phone="+15550000084",
        )
        call = GHLCall.objects.create(
            ghl_call_id="group_auto_call_1",
            ghl_contact_id="group_auto_contact_1",
            ghl_location_id="group_auto_loc_1",
            contact=contact,
            transcript_text="Do you pay for training?",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )
        question = Question.objects.create(
            call=call,
            text="Do you pay for training?",
            speaker_role=GHLCall.SpeakerRole.CUSTOMER,
            start_index=0,
            end_index=25,
        )

        grouped_count = auto_group_questions(Question.objects.filter(pk=question.pk))

        self.assertEqual(grouped_count, 1)
        question.refresh_from_db()
        self.assertEqual(question.unified_question_id, canonical.id)

    def test_sync_call_segments_records_prompt_spec_as_instruction_source(self):
        prompt_spec = PromptSpec.objects.create(
            prompt="Treat transcript segmentation as question, answer, and statement extraction.",
            score=85,
        )
        company = Company.objects.create(name="Prompt Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Sally",
            last_name="Ride",
            email="sally@example.com",
            phone="+15550000009",
        )
        call = GHLCall.objects.create(
            ghl_call_id="call_parse_7",
            ghl_contact_id="ghl_contact_parse_7",
            ghl_location_id="loc_parse_7",
            contact=contact,
            prompt_spec=prompt_spec,
            initiated_by=GHLCall.SpeakerRole.CUSTOMER,
            transcript_text="Hello there. Is training paid? Yes, training is paid.",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )

        created_count = sync_call_segments_from_transcript(call)

        self.assertEqual(created_count, 3)
        call.refresh_from_db()
        segmentation_meta = call.raw_transcription_response.get("segmentation", {})
        self.assertEqual(segmentation_meta.get("prompt"), prompt_spec.prompt)
        self.assertEqual(segmentation_meta.get("prompt_source"), "prompt_spec")
        self.assertEqual(segmentation_meta.get("prompt_spec_id"), prompt_spec.id)
        self.assertEqual(segmentation_meta.get("strategy"), "heuristic_fallback")

    def test_sync_call_segments_uses_active_prompt_spec_when_call_has_no_prompt(self):
        active_prompt = PromptSpec.objects.create(
            name="Default Segmentation Prompt",
            prompt="Use this active prompt for segmentation.",
            is_active=True,
        )
        company = Company.objects.create(name="Active Prompt Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Katherine",
            last_name="Johnson",
            email="katherine@example.com",
            phone="+15550000010",
        )
        call = GHLCall.objects.create(
            ghl_call_id="call_parse_active_1",
            ghl_contact_id="ghl_contact_parse_active_1",
            ghl_location_id="loc_parse_active_1",
            contact=contact,
            initiated_by=GHLCall.SpeakerRole.CUSTOMER,
            transcript_text="Hello there. Is training paid? Yes, training is paid.",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )

        created_count = sync_call_segments_from_transcript(call)

        self.assertEqual(created_count, 3)
        call.refresh_from_db()
        self.assertEqual(call.prompt_spec_id, active_prompt.id)
        segmentation_meta = call.raw_transcription_response.get("segmentation", {})
        self.assertEqual(segmentation_meta.get("prompt"), active_prompt.prompt)
        self.assertEqual(segmentation_meta.get("prompt_source"), "active_prompt_spec")
        self.assertEqual(segmentation_meta.get("prompt_spec_id"), active_prompt.id)

    def test_sync_call_segments_auto_creates_default_prompt_spec_when_none_exist(self):
        company = Company.objects.create(name="Autocreate Prompt Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Dorothy",
            last_name="Vaughan",
            email="dorothy@example.com",
            phone="+15550000011",
        )
        call = GHLCall.objects.create(
            ghl_call_id="call_parse_active_2",
            ghl_contact_id="ghl_contact_parse_active_2",
            ghl_location_id="loc_parse_active_2",
            contact=contact,
            initiated_by=GHLCall.SpeakerRole.CUSTOMER,
            transcript_text="Hello there. Is training paid? Yes, training is paid.",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )

        created_count = sync_call_segments_from_transcript(call)

        self.assertEqual(created_count, 3)
        call.refresh_from_db()
        prompt_spec = PromptSpec.objects.get(pk=call.prompt_spec_id)
        self.assertTrue(prompt_spec.is_active)
        self.assertIn("unified node", prompt_spec.prompt.lower())
        segmentation_meta = call.raw_transcription_response.get("segmentation", {})
        self.assertEqual(segmentation_meta.get("prompt_source"), "active_prompt_spec")
        self.assertEqual(segmentation_meta.get("prompt_spec_id"), prompt_spec.id)


class PromptSpecModelTests(TestCase):
    def test_prompt_spec_auto_names_and_keeps_only_one_active_prompt(self):
        first = PromptSpec.objects.create(
            prompt="First segmentation prompt for testing.",
            is_active=True,
        )
        second = PromptSpec.objects.create(
            prompt="Second segmentation prompt for testing.",
            is_active=True,
        )

        first.refresh_from_db()
        second.refresh_from_db()

        self.assertFalse(first.is_active)
        self.assertTrue(second.is_active)
        self.assertTrue(second.name)


class GHLCallAdminTests(TestCase):
    def test_segment_models_are_registered_with_dedicated_admins(self):
        self.assertIsInstance(site._registry[Question], QuestionAdmin)
        self.assertIsInstance(site._registry[Answer], AnswerAdmin)
        self.assertIsInstance(site._registry[Statement], StatementAdmin)
        self.assertIsInstance(site._registry[CallNote], CallNoteAdmin)
        self.assertIn(GHLCallTranscriptBulkEdit, site._registry)
        self.assertIn(QuestionGroupingReview, site._registry)

    def test_transcript_bulk_edit_admin_entry_redirects_to_bulk_editor(self):
        staff_user = get_user_model().objects.create_user(
            username="ghl_admin_bulk_edit",
            email="ghl_admin_bulk_edit@example.com",
            password="password123",
            is_staff=True,
            is_superuser=True,
        )

        client = Client()
        client.force_login(staff_user)
        response = client.get(reverse("admin:ghl_calls_ghlcalltranscriptbulkedit_changelist"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("ghl_call_bulk_edit"))

    def test_question_grouping_review_admin_entry_redirects_to_review_workspace(self):
        staff_user = get_user_model().objects.create_user(
            username="ghl_admin_grouping_review",
            email="ghl_admin_grouping_review@example.com",
            password="password123",
            is_staff=True,
            is_superuser=True,
        )

        client = Client()
        client.force_login(staff_user)
        response = client.get(reverse("admin:ghl_calls_questiongroupingreview_changelist"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("ghl_question_grouping_review"))

    def test_admin_index_lists_transcript_bulk_edit_under_ghl_calls(self):
        staff_user = get_user_model().objects.create_user(
            username="ghl_admin_index_bulk_edit",
            email="ghl_admin_index_bulk_edit@example.com",
            password="password123",
            is_staff=True,
            is_superuser=True,
        )

        client = Client()
        client.force_login(staff_user)
        response = client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Transcript Bulk Edit")
        self.assertContains(response, reverse("admin:ghl_calls_ghlcalltranscriptbulkedit_changelist"))
        self.assertContains(response, "Question Grouping Review")
        self.assertContains(response, reverse("admin:ghl_calls_questiongroupingreview_changelist"))

    def test_answer_admin_includes_note_count_and_question_context(self):
        admin_obj = site._registry[Answer]
        self.assertIn("question_link", admin_obj.list_display)
        self.assertIn("note_count", admin_obj.list_display)
        self.assertIn("review_link", admin_obj.list_display)
        self.assertIn("audio_link", admin_obj.list_display)
        self.assertIn("question_text_preview", admin_obj.readonly_fields)

    def test_statement_admin_includes_one_click_context_links(self):
        admin_obj = site._registry[Statement]
        self.assertIn("call_link", admin_obj.list_display)
        self.assertIn("review_link", admin_obj.list_display)
        self.assertIn("audio_link", admin_obj.list_display)

    def test_question_admin_includes_answers_inline(self):
        admin_obj = site._registry[Question]
        inline_model_names = [inline.model.__name__ for inline in admin_obj.inlines]
        self.assertIn("Answer", inline_model_names)
        self.assertTrue(issubclass(QuestionAnswerInline, StackedInline))

    def test_question_admin_lists_linked_answers(self):
        admin_obj = site._registry[Question]
        self.assertIn("linked_answers", admin_obj.list_display)
        self.assertNotIn("unified_question", admin_obj.list_display)

        company = Company.objects.create(name="Answer Links Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Ada",
            last_name="Lovelace",
            email="ada-links@example.com",
            phone="+15550000999",
        )
        call = GHLCall.objects.create(
            ghl_call_id="linked_answer_call",
            ghl_contact_id="linked_answer_contact",
            ghl_location_id="linked_answer_loc",
            contact=contact,
            transcript_text="Question answer one answer two",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )
        question = Question.objects.create(
            call=call,
            text="Do you offer weekend classes?",
            start_index=0,
            end_index=28,
        )
        first_answer = Answer.objects.create(
            call=call,
            question=question,
            text="Yes, we do.",
            start_index=29,
            end_index=40,
        )
        second_answer = Answer.objects.create(
            call=call,
            question=question,
            text="They run on Saturdays.",
            start_index=41,
            end_index=65,
        )

        rendered = admin_obj.linked_answers(question)

        self.assertIn(reverse("admin:ghl_calls_answer_change", args=[first_answer.id]), rendered)
        self.assertIn(reverse("admin:ghl_calls_answer_change", args=[second_answer.id]), rendered)
        self.assertIn("Yes, we do.", rendered)
        self.assertIn("They run on Saturdays.", rendered)

    def test_call_note_admin_is_registered_for_global_search(self):
        admin_obj = site._registry[CallNote]
        self.assertIn("call_link", admin_obj.list_display)
        self.assertIn("question_link", admin_obj.list_display)
        self.assertIn("answer_link", admin_obj.list_display)
        self.assertIn("statement_link", admin_obj.list_display)

    def test_call_admin_prioritizes_call_sid_and_legacy_id_is_read_only(self):
        admin_obj = site._registry[GHLCall]
        self.assertEqual(admin_obj.list_display[0], "call_sid")
        self.assertEqual(admin_obj.list_display[1], "ghl_call_id")
        self.assertIn("ghl_call_id", admin_obj.readonly_fields)
        self.assertIn("qa_pairs_summary", admin_obj.readonly_fields)
        self.assertEqual(
            admin_obj.list_display_links,
            ("call_sid", "ghl_call_id", "from_number", "to_number", "processing_status"),
        )

    def test_call_admin_places_linked_qa_in_its_own_section_and_hides_raw_started_at(self):
        admin_obj = site._registry[GHLCall]
        fieldset_titles = [title for title, _ in admin_obj.fieldsets]

        self.assertEqual(
            fieldset_titles,
            ["Identifiers", "Call Details", "Transcription", "Raw Data", "Linked Questions And Answers"],
        )
        self.assertNotIn("raw_started_at", admin_obj.fieldsets[1][1]["fields"])
        self.assertEqual(admin_obj.fieldsets[4][1]["fields"], ("qa_pairs_summary",))

    def test_call_admin_restores_question_and_answer_sections(self):
        admin_obj = site._registry[GHLCall]
        inline_models = [inline.model.__name__ for inline in admin_obj.inlines]

        self.assertEqual(inline_models, ["Question", "Answer", "Statement", "CallNote"])

    def test_unified_node_admins_use_compact_read_only_item_inlines(self):
        question_admin = site._registry[UnifiedNodeQuestion]
        answer_admin = site._registry[UnifiedNodeAnswer]
        statement_admin = site._registry[UnifiedNodeStatement]

        self.assertEqual(question_admin.inlines[0].fields, ("item_link", "text_preview", "speaker_role", "call_link", "start_index", "end_index"))
        self.assertEqual(
            answer_admin.inlines[0].fields,
            ("item_link", "text_preview", "question_link", "speaker_role", "call_link", "start_index", "end_index"),
        )
        self.assertEqual(statement_admin.inlines[0].fields, ("item_link", "text_preview", "speaker_role", "call_link", "start_index", "end_index"))
        self.assertEqual(question_admin.inlines[1].fields, ("name", "created_at", "updated_at"))
        self.assertEqual(answer_admin.inlines[1].fields, ("name", "created_at", "updated_at"))
        self.assertEqual(statement_admin.inlines[1].fields, ("name", "created_at", "updated_at"))
        self.assertIn("name", question_admin.readonly_fields)
        self.assertIn("name", answer_admin.readonly_fields)
        self.assertIn("name", statement_admin.readonly_fields)

    def test_call_admin_change_page_renders_original_question_and_answer_sections(self):
        staff_user = get_user_model().objects.create_user(
            username="ghl_admin",
            email="ghl_admin@example.com",
            password="password123",
            is_staff=True,
            is_superuser=True,
        )
        company = Company.objects.create(name="QA Flow Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            phone="+15550000123",
        )
        call = GHLCall.objects.create(
            ghl_call_id="qa_flow_call",
            ghl_contact_id="qa_flow_contact",
            ghl_location_id="qa_flow_loc",
            contact=contact,
            transcript_text="Question then answer",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )
        question = Question.objects.create(
            call=call,
            text="Is training paid?",
            start_index=0,
            end_index=17,
        )
        Answer.objects.create(
            call=call,
            question=question,
            text="Yes, training is paid.",
            start_index=18,
            end_index=40,
        )

        client = Client()
        client.force_login(staff_user)
        response = client.get(reverse("admin:ghl_calls_ghlcall_change", args=[call.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Questions")
        self.assertContains(response, "Answers")
        self.assertContains(response, "Is training paid?")
        self.assertContains(response, "Yes, training is paid.")
        self.assertContains(response, "Linked Questions And Answers")

    def test_call_admin_change_page_renders_row_by_row_linked_qa_summary(self):
        staff_user = get_user_model().objects.create_user(
            username="ghl_admin_pairs",
            email="ghl_admin_pairs@example.com",
            password="password123",
            is_staff=True,
            is_superuser=True,
        )
        company = Company.objects.create(name="QA Pair Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Marie",
            last_name="Curie",
            email="marie@example.com",
            phone="+15550000125",
        )
        call = GHLCall.objects.create(
            ghl_call_id="qa_pairs_call",
            ghl_contact_id="qa_pairs_contact",
            ghl_location_id="qa_pairs_loc",
            contact=contact,
            transcript_text="Question then answer",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )
        question = Question.objects.create(
            call=call,
            text="When do I start?",
            start_index=0,
            end_index=16,
        )
        Answer.objects.create(
            call=call,
            question=question,
            text="Training starts Monday.",
            start_index=17,
            end_index=40,
        )

        client = Client()
        client.force_login(staff_user)
        response = client.get(reverse("admin:ghl_calls_ghlcall_change", args=[call.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Linked Questions And Answers")
        self.assertContains(response, "When do I start?")
        self.assertContains(response, "Training starts Monday.")

    def test_call_admin_change_page_lists_question_without_linked_answers_separately(self):
        staff_user = get_user_model().objects.create_user(
            username="ghl_admin_no_answer",
            email="ghl_admin_no_answer@example.com",
            password="password123",
            is_staff=True,
            is_superuser=True,
        )
        company = Company.objects.create(name="QA No Answer Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Niels",
            last_name="Bohr",
            email="niels@example.com",
            phone="+15550000126",
        )
        call = GHLCall.objects.create(
            ghl_call_id="qa_no_answer_call",
            ghl_contact_id="qa_no_answer_contact",
            ghl_location_id="qa_no_answer_loc",
            contact=contact,
            transcript_text="When do I start?",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )
        Question.objects.create(
            call=call,
            text="When do I start?",
            start_index=0,
            end_index=16,
        )

        client = Client()
        client.force_login(staff_user)
        response = client.get(reverse("admin:ghl_calls_ghlcall_change", args=[call.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Linked Questions And Answers")
        self.assertContains(response, "Questions Without Linked Answers")
        self.assertContains(response, "When do I start?")

    def test_call_admin_change_page_lists_answer_without_linked_questions_separately(self):
        staff_user = get_user_model().objects.create_user(
            username="ghl_admin_standalone_answer",
            email="ghl_admin_standalone_answer@example.com",
            password="password123",
            is_staff=True,
            is_superuser=True,
        )
        company = Company.objects.create(name="QA Standalone Answer Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="James",
            last_name="Clerk",
            email="james@example.com",
            phone="+15550000127",
        )
        call = GHLCall.objects.create(
            ghl_call_id="qa_standalone_answer_call",
            ghl_contact_id="qa_standalone_answer_contact",
            ghl_location_id="qa_standalone_answer_loc",
            contact=contact,
            transcript_text="Training starts Monday.",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )
        Answer.objects.create(
            call=call,
            text="Training starts Monday.",
            start_index=0,
            end_index=23,
        )

        client = Client()
        client.force_login(staff_user)
        response = client.get(reverse("admin:ghl_calls_ghlcall_change", args=[call.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Answers Without Linked Questions")
        self.assertContains(response, "Training starts Monday.")


class GHLCallReviewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = get_user_model().objects.create_user(
            username="reviewer",
            email="reviewer@example.com",
            password="password123",
            is_staff=True,
        )
        self.client.force_login(self.staff_user)

        company = Company.objects.create(name="Review Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Mae",
            last_name="Jemison",
            email="mae@example.com",
            phone="+15550000111",
        )
        self.call = GHLCall.objects.create(
            ghl_call_id="review_call_1",
            ghl_contact_id="review_contact_1",
            ghl_location_id="review_loc_1",
            contact=contact,
            transcript_text="No training is not paid but you do not have to pay for training.",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )
        self.answer = Answer.objects.create(
            call=self.call,
            text="No training is not paid but you do not have to pay for training.",
            speaker_role=GHLCall.SpeakerRole.EMPLOYEE,
            start_index=0,
            end_index=len(self.call.transcript_text),
        )

    def test_review_page_renders_transcript(self):
        response = self.client.get(reverse("ghl_call_review", args=[self.call.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.call.ghl_call_id)
        self.assertContains(response, "No training is not paid")
        self.assertContains(response, "Full Transcript")

    def test_review_page_renders_parsed_segments_inline_in_transcript_panel(self):
        question = Question.objects.create(
            call=self.call,
            text="Is training paid?",
            speaker_role=GHLCall.SpeakerRole.CUSTOMER,
            start_index=0,
            end_index=17,
        )
        Answer.objects.create(
            call=self.call,
            question=question,
            text="No, training is not paid.",
            speaker_role=GHLCall.SpeakerRole.EMPLOYEE,
            start_index=18,
            end_index=43,
        )
        Statement.objects.create(
            call=self.call,
            text="We are based in Eugene.",
            speaker_role=GHLCall.SpeakerRole.EMPLOYEE,
            start_index=44,
            end_index=68,
        )

        response = self.client.get(reverse("ghl_call_review", args=[self.call.id]))

        self.assertContains(response, 'class="transcript-flow"')
        self.assertContains(response, "Question")
        self.assertContains(response, "Answer")
        self.assertContains(response, "Statement")
        self.assertContains(response, "Is training paid?")
        self.assertContains(response, "No, training is not paid.")
        self.assertContains(response, "We are based in Eugene.")
        self.assertNotContains(response, "Questions And Answers")

    def test_review_page_includes_speed_links_and_segment_filters(self):
        response = self.client.get(reverse("ghl_call_review", args=[self.call.id]))

        self.assertContains(response, "Open Call")
        self.assertContains(response, "Bulk Editor")
        self.assertContains(response, "Search transcript segments")
        self.assertContains(response, "All Types")

    def test_bulk_edit_page_renders_question_workspace(self):
        Question.objects.create(
            call=self.call,
            text="Is training paid?",
            speaker_role=GHLCall.SpeakerRole.CUSTOMER,
            start_index=0,
            end_index=17,
        )

        response = self.client.get(reverse("ghl_call_bulk_edit"), {"kind": "question"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bulk Edit Transcription Segments")
        self.assertContains(response, "Select Questions To Edit")
        self.assertContains(response, "Is training paid?")
        self.assertContains(response, "Find text")
        self.assertContains(response, "Replace with")
        self.assertContains(response, "Apply Changes")

    def test_bulk_edit_post_replaces_selected_segment_text_and_call_transcript(self):
        company = Company.objects.create(name="Bulk Replace Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Katherine",
            last_name="Johnson",
            email="bulk-replace@example.com",
            phone="+15550000112",
        )
        call = GHLCall.objects.create(
            ghl_call_id="bulk_replace_call_1",
            ghl_contact_id="bulk_replace_contact_1",
            ghl_location_id="bulk_replace_loc_1",
            contact=contact,
            transcript_text="Is training paid? Training is paid today.",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )
        question = Question.objects.create(
            call=call,
            text="Is training paid?",
            speaker_role=GHLCall.SpeakerRole.UNKNOWN,
            start_index=0,
            end_index=17,
        )
        answer = Answer.objects.create(
            call=call,
            question=question,
            text="Training is paid today.",
            speaker_role=GHLCall.SpeakerRole.EMPLOYEE,
            start_index=18,
            end_index=len(call.transcript_text),
        )

        response = self.client.post(
            reverse("ghl_call_bulk_edit"),
            data={
                "kind": "answer",
                "q": "",
                "page": "1",
                "segment_ids": [str(answer.id)],
                "find_text": "paid",
                "replacement_text": "covered",
            },
        )

        self.assertEqual(response.status_code, 302)
        call.refresh_from_db()
        question.refresh_from_db()
        answer.refresh_from_db()

        self.assertEqual(answer.text, "Training is covered today.")
        self.assertEqual(call.transcript_text, "Is training paid? Training is covered today.")
        self.assertEqual(question.start_index, 0)
        self.assertEqual(question.end_index, 17)
        self.assertEqual(answer.start_index, 18)
        self.assertEqual(answer.end_index, len(call.transcript_text))

    def test_bulk_edit_post_returns_error_when_selected_segments_do_not_match_find_text(self):
        response = self.client.post(
            reverse("ghl_call_bulk_edit"),
            data={
                "kind": "answer",
                "q": "",
                "page": "1",
                "segment_ids": [str(self.answer.id)],
                "find_text": "banana",
                "replacement_text": "orange",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "None of the selected segments contained that text.")

    def test_review_note_endpoint_creates_note_with_answer_link(self):
        response = self.client.post(
            reverse("ghl_call_review_create_note", args=[self.call.id]),
            data=json.dumps(
                {
                    "start_index": 3,
                    "end_index": 11,
                    "edit_option": CallNote.EditOption.DELETE,
                    "negative_impact_score": -20,
                    "original_text": "training",
                    "replacement_text": "",
                    "note": "Delete this misleading word.",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        note = CallNote.objects.get(call=self.call)
        self.assertEqual(note.start_index, 3)
        self.assertEqual(note.end_index, 11)
        self.assertEqual(note.original_text, "training")
        self.assertEqual(note.negative_impact_score, -20)
        self.assertEqual(note.answer_id, self.answer.id)


class QuestionGroupingReviewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = get_user_model().objects.create_user(
            username="grouping-reviewer",
            email="grouping-reviewer@example.com",
            password="password123",
            is_staff=True,
        )
        self.client.force_login(self.staff_user)

        company = Company.objects.create(name="Grouping Co")
        contact = Contact.objects.create(
            company=company,
            role="customer",
            first_name="Lise",
            last_name="Meitner",
            email="lise@example.com",
            phone="+15550000128",
        )
        self.call = GHLCall.objects.create(
            ghl_call_id="grouping_call_1",
            ghl_contact_id="grouping_contact_1",
            ghl_location_id="grouping_loc_1",
            contact=contact,
            transcript_text="Do you pay for training?",
            processing_status=GHLCall.ProcessingStatus.TRANSCRIBED,
        )
        self.question = Question.objects.create(
            call=self.call,
            text="Do you pay for training?",
            speaker_role=GHLCall.SpeakerRole.CUSTOMER,
            start_index=0,
            end_index=25,
        )

    def test_grouping_review_page_renders_question_and_suggestions(self):
        canonical = UnifiedNodeQuestion.objects.create(name="Is training paid")
        ensure_unified_question_alias(canonical, "Do you pay for training")

        response = self.client.get(reverse("ghl_question_grouping_review"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Question Grouping Review")
        self.assertContains(response, self.question.text)
        self.assertContains(response, canonical.name)
        self.assertContains(response, "Assign to this node")

    def test_grouping_review_assign_existing_links_question_and_creates_alias(self):
        canonical = UnifiedNodeQuestion.objects.create(name="Is training paid")

        response = self.client.post(
            reverse("ghl_question_grouping_review"),
            data={
                "question_id": str(self.question.id),
                "action": "assign_existing",
                "unified_question_id": str(canonical.id),
                "q": "",
                "show": "ungrouped",
                "page": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.unified_question_id, canonical.id)
        self.assertTrue(
            UnifiedNodeQuestionAlias.objects.filter(
                unified_question=canonical,
                name="Do you pay for training",
            ).exists()
        )

    def test_grouping_review_can_auto_group_current_filter(self):
        canonical = UnifiedNodeQuestion.objects.create(name="Is training paid")

        response = self.client.post(
            reverse("ghl_question_grouping_review"),
            data={
                "action": "auto_group_matches",
                "q": "",
                "show": "ungrouped",
                "page": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.unified_question_id, canonical.id)

    def test_grouping_review_create_new_makes_canonical_question(self):
        response = self.client.post(
            reverse("ghl_question_grouping_review"),
            data={
                "question_id": str(self.question.id),
                "action": "create_new",
                "new_name": "Is training paid",
                "q": "",
                "show": "ungrouped",
                "page": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.question.refresh_from_db()
        self.assertEqual(self.question.unified_question.name, "Is training paid")
        self.assertTrue(
            UnifiedNodeQuestionAlias.objects.filter(
                unified_question=self.question.unified_question,
                name="Do you pay for training",
            ).exists()
        )


@override_settings(GHL_CALLS_ALLOW_UNSIGNED_WEBHOOKS=True)
class GHLCallWebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("ghl_call_webhook")
        self.company = Company.objects.create(name="Test Company")
        self.contact = Contact.objects.create(
            company=self.company,
            role="customer",
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            phone="+15550000002",
            privser_contact_id="ghl_contact_1",
        )

    def test_non_call_event_is_ignored(self):
        payload = {
            "type": "OutboundMessage",
            "messageType": "SMS",
            "messageId": "msg_1",
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["ignored"], True)
        self.assertEqual(GHLCall.objects.count(), 0)
        self.assertEqual(GHLCallWebhookEvent.objects.count(), 0)

    def test_call_event_creates_call(self):
        payload = {
            "type": "OutboundMessage",
            "id": "evt_2",
            "callSid": "CA456",
            "messageId": "call_456",
            "contactId": "ghl_contact_1",
            "locationId": "loc_1",
            "direction": "outbound",
            "callStatus": "completed",
            "messageType": "CALL",
            "from": "+15550000001",
            "to": "+15550000002",
            "attachments": ["https://example.com/audio.mp3"],
            "callDuration": 93,
            "dateAdded": "2026-03-22T10:30:00Z",
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertTrue(body["stored"])
        self.assertFalse(body["transcription_saved"])

        call = GHLCall.objects.get(call_sid="CA456")
        self.assertEqual(call.ghl_call_id, "call_456")
        self.assertEqual(call.contact, self.contact)
        self.assertEqual(call.recording_url, "https://example.com/audio.mp3")
        self.assertEqual(call.recording_duration_seconds, 93)

        event = GHLCallWebhookEvent.objects.get(call=call)
        self.assertEqual(event.event_type, "OutboundMessage")
        self.assertEqual(event.event_id, "evt_2")

    def test_call_event_without_recording_is_stored(self):
        payload = {
            "type": "OutboundMessage",
            "id": "evt_3",
            "callSid": "CA789",
            "messageId": "call_789",
            "contactId": "ghl_contact_1",
            "locationId": "loc_1",
            "direction": "inbound",
            "callStatus": "missed",
            "messageType": "CALL",
            "from": "+15550000001",
            "to": "+15550000002",
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertTrue(body["stored"])
        self.assertFalse(body["transcription_saved"])

        call = GHLCall.objects.get(call_sid="CA789")
        self.assertEqual(call.recording_url, "")

    def test_call_event_without_call_sid_uses_legacy_call_id(self):
        payload = {
            "type": "OutboundMessage",
            "id": "evt_legacy",
            "messageId": "legacy_call_1",
            "contactId": "ghl_contact_1",
            "locationId": "loc_1",
            "direction": "outbound",
            "callStatus": "completed",
            "messageType": "CALL",
            "from": "+15550000001",
            "to": "+15550000002",
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 202)
        call = GHLCall.objects.get(ghl_call_id="legacy_call_1")
        self.assertEqual(call.call_sid, "")

    def test_transcript_workflow_webhook_updates_existing_call(self):
        GHLCall.objects.create(
            ghl_call_id="call_999",
            call_sid="CA999",
            ghl_contact_id="ghl_contact_1",
            ghl_location_id="loc_1",
            contact=self.contact,
            direction="outbound",
            status="completed",
        )

        payload = {
            "callSid": "CA999",
            "messageId": "call_999",
            "contactId": "ghl_contact_1",
            "locationId": "loc_1",
            "transcriptText": "This is the workflow transcript",
            "status": "completed",
        }

        response = self.client.post(
            reverse("ghl_transcript_webhook"),
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertTrue(body["transcript_saved"])

        call = GHLCall.objects.get(call_sid="CA999")
        self.assertEqual(call.transcript_text, "This is the workflow transcript")
        self.assertEqual(call.processing_status, GHLCall.ProcessingStatus.TRANSCRIBED)
        self.assertEqual(call.initiated_by, GHLCall.SpeakerRole.UNKNOWN)

    def test_transcript_workflow_webhook_updates_existing_call_by_legacy_call_id(self):
        GHLCall.objects.create(
            ghl_call_id="legacy_call_2",
            ghl_contact_id="ghl_contact_1",
            ghl_location_id="loc_1",
            contact=self.contact,
            direction="outbound",
            status="completed",
        )

        payload = {
            "messageId": "legacy_call_2",
            "contactId": "ghl_contact_1",
            "locationId": "loc_1",
            "transcriptText": "Legacy id transcript update",
            "status": "completed",
        }

        response = self.client.post(
            reverse("ghl_transcript_webhook"),
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 202)
        call = GHLCall.objects.get(ghl_call_id="legacy_call_2")
        self.assertEqual(call.transcript_text, "Legacy id transcript update")
        self.assertEqual(call.processing_status, GHLCall.ProcessingStatus.TRANSCRIBED)

    def test_transcript_workflow_webhook_creates_segments(self):
        GHLCall.objects.create(
            ghl_call_id="call_1000",
            call_sid="CA1000",
            ghl_contact_id="ghl_contact_1",
            ghl_location_id="loc_1",
            contact=self.contact,
            direction="outbound",
            status="completed",
        )

        payload = {
            "callSid": "CA1000",
            "messageId": "call_1000",
            "contactId": "ghl_contact_1",
            "locationId": "loc_1",
            "transcriptText": "Hello. When are you open? We are open from nine to five.",
            "status": "completed",
        }

        response = self.client.post(
            reverse("ghl_transcript_webhook"),
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 202)
        call = GHLCall.objects.get(call_sid="CA1000")
        self.assertEqual(call.questions.count(), 1)
        self.assertEqual(call.answers.count(), 1)
        self.assertEqual(call.statements.count(), 1)

    def test_call_event_sets_initiated_by_from_direction(self):
        payload = {
            "type": "OutboundMessage",
            "id": "evt_4",
            "callSid": "CA321",
            "messageId": "call_321",
            "contactId": "ghl_contact_1",
            "locationId": "loc_1",
            "direction": "outbound",
            "callStatus": "completed",
            "messageType": "CALL",
            "from": "+15550000001",
            "to": "+15550000002",
        }

        response = self.client.post(
            self.url,
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 202)
        call = GHLCall.objects.get(call_sid="CA321")
        self.assertEqual(call.initiated_by, GHLCall.SpeakerRole.EMPLOYEE)
