from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

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
    UnifiedNodeAnswerAlias,
    UnifiedNodeQuestion,
    UnifiedNodeQuestionAlias,
    UnifiedNodeStatement,
    UnifiedNodeStatementAlias,
)


class SegmentAdminMixin:
    readonly_fields = ("call_link", "review_link", "audio_link", "question_link", "question_text_preview")

    def call_link(self, obj):
        if not getattr(obj, "call_id", None):
            return "-"
        url = reverse("admin:ghl_calls_ghlcall_change", args=[obj.call_id])
        label = obj.call.call_sid or obj.call.ghl_call_id
        return format_html('<a href="{}">{}</a>', url, label)

    call_link.short_description = "Call"

    def review_link(self, obj):
        if not getattr(obj, "call_id", None):
            return "-"
        url = reverse("ghl_call_review", args=[obj.call_id])
        return format_html('<a href="{}" target="_blank">Open review page</a>', url)

    review_link.short_description = "Review"

    def audio_link(self, obj):
        call = getattr(obj, "call", None)
        if not call:
            return "-"
        if call.recording_url:
            return format_html('<a href="{}" target="_blank">Open recording URL</a>', call.recording_url)
        return "-"

    audio_link.short_description = "Audio"

    def question_link(self, obj):
        question = getattr(obj, "question", None)
        if not question:
            return "-"
        url = reverse("admin:ghl_calls_question_change", args=[question.id])
        label = question.text[:80]
        return format_html('<a href="{}">{}</a>', url, label)

    question_link.short_description = "Question"

    def question_text_preview(self, obj):
        question = getattr(obj, "question", None)
        if not question:
            return "-"
        return question.text

    question_text_preview.short_description = "Question text"

    def answer_link(self, obj):
        answer = getattr(obj, "answer", None)
        if not answer:
            return "-"
        url = reverse("admin:ghl_calls_answer_change", args=[answer.id])
        label = answer.text[:80]
        return format_html('<a href="{}">{}</a>', url, label)

    answer_link.short_description = "Answer"

    def statement_link(self, obj):
        statement = getattr(obj, "statement", None)
        if not statement:
            return "-"
        url = reverse("admin:ghl_calls_statement_change", args=[statement.id])
        label = statement.text[:80]
        return format_html('<a href="{}">{}</a>', url, label)

    statement_link.short_description = "Statement"


class UnifiedNodeItemInlineMixin:
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = (
        "speaker_role",
        "text",
        "ai_accuracy_score",
        "human_accuracy_score",
        "start_index",
        "end_index",
        "unified_question",
    )


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = (
        "speaker_role",
        "text",
        "ai_accuracy_score",
        "human_accuracy_score",
        "start_index",
        "end_index",
        "unified_answer",
    )


class QuestionAnswerInline(admin.StackedInline):
    model = Answer
    fk_name = "question"
    extra = 0
    readonly_fields = ("call_link", "review_link", "audio_link")
    fields = (
        ("call_link", "review_link", "audio_link"),
        "speaker_role",
        "text",
        "unified_answer",
        ("ai_accuracy_score", "human_accuracy_score"),
        ("start_index", "end_index"),
        "call",
    )
    autocomplete_fields = ("call", "unified_answer")

    def call_link(self, obj):
        if not obj or not obj.pk or not obj.call_id:
            return "-"
        url = reverse("admin:ghl_calls_ghlcall_change", args=[obj.call_id])
        label = obj.call.call_sid or obj.call.ghl_call_id
        return format_html('<a href="{}">{}</a>', url, label)

    call_link.short_description = "Call"

    def review_link(self, obj):
        if not obj or not obj.pk or not obj.call_id:
            return "-"
        url = reverse("ghl_call_review", args=[obj.call_id])
        return format_html('<a href="{}" target="_blank">Open review page</a>', url)

    review_link.short_description = "Review"

    def audio_link(self, obj):
        if not obj or not obj.pk or not obj.call_id:
            return "-"
        if obj.call.recording_url:
            return format_html('<a href="{}" target="_blank">Open recording URL</a>', obj.call.recording_url)
        return "-"

    audio_link.short_description = "Audio"


class StatementInline(admin.TabularInline):
    model = Statement
    extra = 0
    fields = (
        "speaker_role",
        "text",
        "ai_accuracy_score",
        "human_accuracy_score",
        "start_index",
        "end_index",
        "unified_statement",
    )


class CallNoteInline(admin.TabularInline):
    model = CallNote
    extra = 0
    fields = (
        "start_index",
        "end_index",
        "edit_option",
        "negative_impact_score",
        "original_text",
        "replacement_text",
        "note",
        "question",
        "answer",
        "statement",
    )


class QuestionCallNoteInline(admin.TabularInline):
    model = CallNote
    fk_name = "question"
    extra = 0
    fields = (
        "call",
        "start_index",
        "end_index",
        "edit_option",
        "negative_impact_score",
        "original_text",
        "replacement_text",
        "note",
    )
    autocomplete_fields = ("call",)


class AnswerCallNoteInline(admin.TabularInline):
    model = CallNote
    fk_name = "answer"
    extra = 0
    fields = (
        "call",
        "start_index",
        "end_index",
        "edit_option",
        "negative_impact_score",
        "original_text",
        "replacement_text",
        "note",
    )
    autocomplete_fields = ("call",)


class StatementCallNoteInline(admin.TabularInline):
    model = CallNote
    fk_name = "statement"
    extra = 0
    fields = (
        "call",
        "start_index",
        "end_index",
        "edit_option",
        "negative_impact_score",
        "original_text",
        "replacement_text",
        "note",
    )
    autocomplete_fields = ("call",)


class UnifiedQuestionInline(UnifiedNodeItemInlineMixin, admin.TabularInline):
    model = Question
    fields = ("item_link", "text_preview", "speaker_role", "call_link", "start_index", "end_index")
    readonly_fields = fields

    def item_link(self, obj):
        if not obj or not obj.pk:
            return "-"
        url = reverse("admin:ghl_calls_question_change", args=[obj.pk])
        return format_html('<a href="{}">Open question</a>', url)

    item_link.short_description = "Item"

    def text_preview(self, obj):
        if not obj or not obj.pk:
            return "-"
        return format_html("<details><summary>{}</summary><div>{}</div></details>", obj.text[:90], obj.text)

    text_preview.short_description = "Question"

    def call_link(self, obj):
        if not obj or not obj.pk or not obj.call_id:
            return "-"
        url = reverse("admin:ghl_calls_ghlcall_change", args=[obj.call_id])
        label = obj.call.call_sid or obj.call.ghl_call_id
        return format_html('<a href="{}">{}</a>', url, label)

    call_link.short_description = "Call"


class UnifiedQuestionAliasInline(admin.TabularInline):
    model = UnifiedNodeQuestionAlias
    extra = 0
    fields = ("name", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


class UnifiedAnswerInline(UnifiedNodeItemInlineMixin, admin.TabularInline):
    model = Answer
    fields = (
        "item_link",
        "text_preview",
        "question_link",
        "speaker_role",
        "call_link",
        "start_index",
        "end_index",
    )
    readonly_fields = fields

    def item_link(self, obj):
        if not obj or not obj.pk:
            return "-"
        url = reverse("admin:ghl_calls_answer_change", args=[obj.pk])
        return format_html('<a href="{}">Open answer</a>', url)

    item_link.short_description = "Item"

    def text_preview(self, obj):
        if not obj or not obj.pk:
            return "-"
        return format_html("<details><summary>{}</summary><div>{}</div></details>", obj.text[:90], obj.text)

    text_preview.short_description = "Answer"

    def question_link(self, obj):
        if not obj or not obj.pk or not obj.question_id:
            return "-"
        url = reverse("admin:ghl_calls_question_change", args=[obj.question_id])
        return format_html('<a href="{}">{}</a>', url, obj.question.text[:80])

    question_link.short_description = "Question"

    def call_link(self, obj):
        if not obj or not obj.pk or not obj.call_id:
            return "-"
        url = reverse("admin:ghl_calls_ghlcall_change", args=[obj.call_id])
        label = obj.call.call_sid or obj.call.ghl_call_id
        return format_html('<a href="{}">{}</a>', url, label)

    call_link.short_description = "Call"


class UnifiedAnswerAliasInline(admin.TabularInline):
    model = UnifiedNodeAnswerAlias
    extra = 0
    fields = ("name", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


class UnifiedStatementInline(UnifiedNodeItemInlineMixin, admin.TabularInline):
    model = Statement
    fields = ("item_link", "text_preview", "speaker_role", "call_link", "start_index", "end_index")
    readonly_fields = fields

    def item_link(self, obj):
        if not obj or not obj.pk:
            return "-"
        url = reverse("admin:ghl_calls_statement_change", args=[obj.pk])
        return format_html('<a href="{}">Open statement</a>', url)

    item_link.short_description = "Item"

    def text_preview(self, obj):
        if not obj or not obj.pk:
            return "-"
        return format_html("<details><summary>{}</summary><div>{}</div></details>", obj.text[:90], obj.text)

    text_preview.short_description = "Statement"

    def call_link(self, obj):
        if not obj or not obj.pk or not obj.call_id:
            return "-"
        url = reverse("admin:ghl_calls_ghlcall_change", args=[obj.call_id])
        label = obj.call.call_sid or obj.call.ghl_call_id
        return format_html('<a href="{}">{}</a>', url, label)

    call_link.short_description = "Call"


class UnifiedStatementAliasInline(admin.TabularInline):
    model = UnifiedNodeStatementAlias
    extra = 0
    fields = ("name", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CallNote)
class CallNoteAdmin(SegmentAdminMixin, admin.ModelAdmin):
    list_display = (
        "call_link",
        "question_link",
        "answer_link",
        "statement_link",
        "edit_option",
        "negative_impact_score",
        "original_text",
        "replacement_text",
        "start_index",
        "end_index",
    )
    list_filter = ("edit_option", "call__ghl_location_id", "created_at")
    search_fields = (
        "note",
        "original_text",
        "replacement_text",
        "call__ghl_call_id",
        "call__call_sid",
        "question__text",
        "answer__text",
        "statement__text",
    )
    autocomplete_fields = ("call", "question", "answer", "statement")
    readonly_fields = (
        "call_link",
        "question_link",
        "answer_link",
        "statement_link",
        "review_link",
        "audio_link",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Context",
            {
                "fields": (
                    "call_link",
                    "question_link",
                    "answer_link",
                    "statement_link",
                    "review_link",
                    "audio_link",
                )
            },
        ),
        (
            "Note",
            {
                "fields": (
                    "call",
                    "question",
                    "answer",
                    "statement",
                    "start_index",
                    "end_index",
                    "edit_option",
                    "negative_impact_score",
                    "original_text",
                    "replacement_text",
                    "note",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )


@admin.register(GHLCall)
class GHLCallAdmin(admin.ModelAdmin):
    list_display = (
        "call_sid",
        "ghl_call_id",
        "prompt_spec",
        "initiated_by",
        "direction",
        "status",
        "processing_status",
        "from_number",
        "to_number",
        "question_count",
        "answer_count",
        "statement_count",
        "note_count",
        "review_link",
        "created_at",
    )
    list_display_links = ("call_sid", "ghl_call_id", "from_number", "to_number", "processing_status")
    search_fields = (
        "call_sid",
        "ghl_call_id",
        "ghl_contact_id",
        "from_number",
        "to_number",
    )
    list_filter = ("initiated_by", "direction", "status", "processing_status", "created_at")
    readonly_fields = (
        "ghl_call_id",
        "created_at",
        "updated_at",
        "last_webhook_received_at",
        "review_link",
        "qa_pairs_summary",
    )
    inlines = [QuestionInline, AnswerInline, StatementInline, CallNoteInline]
    autocomplete_fields = ("contact", "prompt_spec")
    fieldsets = (
        (
            "Identifiers",
            {
                "fields": (
                    "call_sid",
                    "ghl_call_id",
                    "ghl_contact_id",
                    "ghl_location_id",
                    "contact",
                    "prompt_spec",
                )
            },
        ),
        (
            "Call Details",
            {
                "fields": (
                    "initiated_by",
                    "direction",
                    "status",
                    "from_number",
                    "to_number",
                    "recording_url",
                    "recording_duration_seconds",
                    "started_at",
                    "ended_at",
                    "raw_ended_at",
                )
            },
        ),
        (
            "Transcription",
            {
                "fields": (
                    "processing_status",
                    "transcription_model",
                    "transcript_text",
                    "transcription_error",
                )
            },
        ),
        (
            "Raw Data",
            {
                "classes": ("collapse",),
                "fields": (
                    "raw_transcription_response",
                    "raw_payload",
                    "raw_recording_metadata",
                    "last_webhook_received_at",
                    "created_at",
                    "updated_at",
                    "review_link",
                ),
            },
        ),
        (
            "Linked Questions And Answers",
            {
                "fields": ("qa_pairs_summary",),
            },
        ),
    )

    def question_count(self, obj):
        return obj.questions.count()

    question_count.short_description = "Questions"

    def answer_count(self, obj):
        return obj.answers.count()

    answer_count.short_description = "Answers"

    def statement_count(self, obj):
        return obj.statements.count()

    statement_count.short_description = "Statements"

    def note_count(self, obj):
        return obj.notes.count()

    note_count.short_description = "Notes"

    def review_link(self, obj):
        url = reverse("ghl_call_review", args=[obj.id])
        return format_html('<a href="{}" target="_blank">Open review page</a>', url)

    review_link.short_description = "Review"

    def qa_pairs_summary(self, obj):
        if not obj or not obj.pk:
            return "Save the call first to see linked questions and answers."

        rows = []
        unpaired_questions = []
        questions = obj.questions.order_by("start_index", "id").prefetch_related("answers")
        for question in questions:
            answers = list(question.answers.order_by("start_index", "id"))
            if not answers:
                unpaired_questions.append(question)
                continue

            answer_cell = format_html_join(
                "",
                '<div style="margin:0 0 8px 0;"><a href="{}">{}</a></div>',
                (
                    (reverse("admin:ghl_calls_answer_change", args=[answer.id]), answer.text[:240])
                    for answer in answers
                ),
            )

            rows.append(
                format_html(
                    """
                    <tr>
                        <td style="vertical-align:top; padding:10px 12px; border:1px solid #e5dfd3;">
                            <a href="{}">{}</a>
                        </td>
                        <td style="vertical-align:top; padding:10px 12px; border:1px solid #e5dfd3;">
                            {}
                        </td>
                    </tr>
                    """,
                    reverse("admin:ghl_calls_question_change", args=[question.id]),
                    question.text[:240],
                    answer_cell,
                )
            )

        standalone_answers = list(obj.answers.filter(question__isnull=True).order_by("start_index", "id"))

        sections = []

        if rows:
            sections.append(
                format_html(
                    """
                    <table style="width:100%; border-collapse:collapse; margin:8px 0 16px 0;">
                        <thead>
                            <tr>
                                <th style="text-align:left; padding:8px 12px; border:1px solid #d8d2c5; background:#f7f3ea;">Question</th>
                                <th style="text-align:left; padding:8px 12px; border:1px solid #d8d2c5; background:#f7f3ea;">Answer</th>
                            </tr>
                        </thead>
                        <tbody>{}</tbody>
                    </table>
                    """,
                    mark_safe("".join(str(row) for row in rows)),
                )
            )

        if unpaired_questions:
            sections.append(
                format_html(
                    """
                    <div style="margin:0 0 16px 0;">
                        <div style="font-weight:600; margin:0 0 8px 0;">Questions Without Linked Answers</div>
                        <div>{}</div>
                    </div>
                    """,
                    format_html_join(
                        "",
                        '<div style="margin:0 0 8px 0;"><a href="{}">{}</a></div>',
                        (
                            (reverse("admin:ghl_calls_question_change", args=[question.id]), question.text[:240])
                            for question in unpaired_questions
                        ),
                    ),
                )
            )

        if standalone_answers:
            sections.append(
                format_html(
                    """
                    <div style="margin:0 0 8px 0;">
                        <div style="font-weight:600; margin:0 0 8px 0;">Answers Without Linked Questions</div>
                        <div>{}</div>
                    </div>
                    """,
                    format_html_join(
                        "",
                        '<div style="margin:0 0 8px 0;"><a href="{}">{}</a></div>',
                        (
                            (reverse("admin:ghl_calls_answer_change", args=[answer.id]), answer.text[:240])
                            for answer in standalone_answers
                        ),
                    ),
                )
            )

        if not sections:
            return "No linked questions and answers yet."

        return mark_safe("".join(str(section) for section in sections))

    qa_pairs_summary.short_description = "Linked Questions And Answers"


@admin.register(GHLCallTranscriptBulkEdit)
class GHLCallTranscriptBulkEditAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return bool(request.user and request.user.is_active and request.user.is_staff)

    def has_view_permission(self, request, obj=None):
        return bool(request.user and request.user.is_active and request.user.is_staff)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj=obj)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_model_perms(self, request):
        if not self.has_module_permission(request):
            return {}
        return {
            "add": False,
            "change": True,
            "delete": False,
            "view": True,
        }

    def changelist_view(self, request, extra_context=None):
        return HttpResponseRedirect(reverse("ghl_call_bulk_edit"))


@admin.register(QuestionGroupingReview)
class QuestionGroupingReviewAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return bool(request.user and request.user.is_active and request.user.is_staff)

    def has_view_permission(self, request, obj=None):
        return bool(request.user and request.user.is_active and request.user.is_staff)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj=obj)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_model_perms(self, request):
        if not self.has_module_permission(request):
            return {}
        return {
            "add": False,
            "change": True,
            "delete": False,
            "view": True,
        }

    def changelist_view(self, request, extra_context=None):
        return HttpResponseRedirect(reverse("ghl_question_grouping_review"))


@admin.register(GHLCallWebhookEvent)
class GHLCallWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "event_id", "call", "received_at", "processed_at")
    search_fields = ("event_type", "event_id", "signature")
    list_filter = ("event_type", "received_at", "processed_at")
    readonly_fields = ("received_at",)
    autocomplete_fields = ("call",)


@admin.register(UnifiedNodeQuestion)
class UnifiedNodeQuestionAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    readonly_fields = ("name", "created_at", "updated_at")
    fields = ("name", "created_at", "updated_at")
    inlines = [UnifiedQuestionInline, UnifiedQuestionAliasInline]


@admin.register(UnifiedNodeAnswer)
class UnifiedNodeAnswerAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    readonly_fields = ("name", "created_at", "updated_at")
    fields = ("name", "created_at", "updated_at")
    inlines = [UnifiedAnswerInline, UnifiedAnswerAliasInline]


@admin.register(UnifiedNodeStatement)
class UnifiedNodeStatementAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    readonly_fields = ("name", "created_at", "updated_at")
    fields = ("name", "created_at", "updated_at")
    inlines = [UnifiedStatementInline, UnifiedStatementAliasInline]


@admin.register(PromptSpec)
class PromptSpecAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "score", "response_time", "token_cost", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "prompt")
    readonly_fields = ("created_at", "updated_at")
    actions = ("make_active_prompt",)

    def make_active_prompt(self, request, queryset):
        prompt_spec = queryset.order_by("-updated_at", "-id").first()
        if not prompt_spec:
            return
        queryset.update(is_active=False)
        prompt_spec.is_active = True
        prompt_spec.save(update_fields=["is_active", "updated_at"])
        self.message_user(request, f'"{prompt_spec}" is now the active prompt.')

    make_active_prompt.short_description = "Make selected prompt the active default"


@admin.register(Question)
class QuestionAdmin(SegmentAdminMixin, admin.ModelAdmin):
    list_display = (
        "short_text",
        "call_link",
        "speaker_role",
        "human_accuracy_score",
        "ai_accuracy_score",
        "start_index",
        "end_index",
        "linked_answers",
        "note_count",
        "review_link",
        "audio_link",
    )
    list_filter = ("speaker_role", "call__ghl_location_id", "created_at")
    search_fields = ("text", "call__ghl_call_id", "call__ghl_contact_id", "unified_question__name")
    autocomplete_fields = ("call", "unified_question")
    inlines = [QuestionAnswerInline, QuestionCallNoteInline]
    fieldsets = (
        (
            "Context",
            {"fields": ("call_link", "review_link", "audio_link", "speaker_role")},
        ),
        (
            "Question",
            {
                "fields": (
                    "text",
                    "unified_question",
                    "ai_accuracy_score",
                    "human_accuracy_score",
                    "start_index",
                    "end_index",
                    "call",
                )
            },
        ),
    )

    def short_text(self, obj):
        return obj.text[:80]

    short_text.short_description = "Question"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("answers")

    def linked_answers(self, obj):
        answers = list(obj.answers.order_by("start_index", "id"))
        if not answers:
            return "-"
        return format_html_join(
            "<br>",
            '<a href="{}">{}</a>',
            (
                (
                    reverse("admin:ghl_calls_answer_change", args=[answer.id]),
                    answer.text[:80] or f"Answer {answer.id}",
                )
                for answer in answers
            ),
        )

    linked_answers.short_description = "Linked Answers"

    def note_count(self, obj):
        return obj.notes.count()

    note_count.short_description = "Notes"


@admin.register(Answer)
class AnswerAdmin(SegmentAdminMixin, admin.ModelAdmin):
    list_display = (
        "short_text",
        "call_link",
        "question_link",
        "speaker_role",
        "human_accuracy_score",
        "ai_accuracy_score",
        "start_index",
        "end_index",
        "unified_answer",
        "note_count",
        "review_link",
        "audio_link",
    )
    list_filter = ("speaker_role", "call__ghl_location_id", "created_at")
    search_fields = (
        "text",
        "call__ghl_call_id",
        "call__ghl_contact_id",
        "question__text",
        "unified_answer__name",
    )
    autocomplete_fields = ("call", "question", "unified_answer")
    inlines = [AnswerCallNoteInline]
    fieldsets = (
        (
            "Context",
            {
                "fields": (
                    "call_link",
                    ("question_link", "review_link", "audio_link"),
                    "question_text_preview",
                    "speaker_role",
                )
            },
        ),
        (
            "Answer",
            {
                "fields": (
                    "text",
                    "unified_answer",
                    "ai_accuracy_score",
                    "human_accuracy_score",
                    "start_index",
                    "end_index",
                    "call",
                    "question",
                )
            },
        ),
    )

    def short_text(self, obj):
        return obj.text[:80]

    short_text.short_description = "Answer"

    def note_count(self, obj):
        return obj.notes.count()

    note_count.short_description = "Notes"


@admin.register(Statement)
class StatementAdmin(SegmentAdminMixin, admin.ModelAdmin):
    list_display = (
        "short_text",
        "call_link",
        "speaker_role",
        "human_accuracy_score",
        "ai_accuracy_score",
        "start_index",
        "end_index",
        "unified_statement",
        "note_count",
        "review_link",
        "audio_link",
    )
    list_filter = ("speaker_role", "call__ghl_location_id", "created_at")
    search_fields = ("text", "call__ghl_call_id", "call__ghl_contact_id", "unified_statement__name")
    autocomplete_fields = ("call", "unified_statement")
    inlines = [StatementCallNoteInline]
    fieldsets = (
        (
            "Context",
            {"fields": ("call_link", "review_link", "audio_link", "speaker_role")},
        ),
        (
            "Statement",
            {
                "fields": (
                    "text",
                    "unified_statement",
                    "ai_accuracy_score",
                    "human_accuracy_score",
                    "start_index",
                    "end_index",
                    "call",
                )
            },
        ),
    )

    def short_text(self, obj):
        return obj.text[:80]

    short_text.short_description = "Statement"

    def note_count(self, obj):
        return obj.notes.count()

    note_count.short_description = "Notes"
