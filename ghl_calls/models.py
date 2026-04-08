from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class GHLCall(models.Model):
    class SpeakerRole(models.TextChoices):
        EMPLOYEE = "employee", "Employee"
        CUSTOMER = "customer", "Customer"
        UNKNOWN = "unknown", "Unknown"

    class Direction(models.TextChoices):
        INBOUND = "inbound", "Inbound"
        OUTBOUND = "outbound", "Outbound"
        UNKNOWN = "unknown", "Unknown"

    class ProcessingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        DOWNLOADED = "downloaded", "Downloaded"
        TRANSCRIBED = "transcribed", "Transcribed"
        FAILED = "failed", "Failed"

    ghl_call_id = models.CharField(max_length=128, unique=True, db_index=True)
    call_sid = models.CharField(max_length=128, blank=True, db_index=True)
    ghl_contact_id = models.CharField(max_length=128, blank=True, db_index=True)
    ghl_location_id = models.CharField(max_length=128, blank=True, db_index=True)

    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ghl_calls",
    )
    prompt_spec = models.ForeignKey(
        "ghl_calls.PromptSpec",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calls",
    )

    direction = models.CharField(
        max_length=20,
        choices=Direction.choices,
        default=Direction.UNKNOWN,
    )
    initiated_by = models.CharField(
        max_length=20,
        choices=SpeakerRole.choices,
        default=SpeakerRole.UNKNOWN,
    )
    status = models.CharField(max_length=64, blank=True, db_index=True)

    from_number = models.CharField(max_length=50, blank=True, db_index=True)
    to_number = models.CharField(max_length=50, blank=True, db_index=True)

    recording_url = models.URLField(max_length=1000, blank=True)
    recording_duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    raw_started_at = models.CharField(max_length=255, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    raw_ended_at = models.CharField(max_length=255, blank=True)

    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        db_index=True,
    )
    transcription_model = models.CharField(max_length=100, blank=True)
    transcript_text = models.TextField(blank=True)
    transcription_error = models.TextField(blank=True)
    raw_transcription_response = models.JSONField(default=dict, blank=True)

    raw_payload = models.JSONField(default=dict, blank=True)
    raw_recording_metadata = models.JSONField(default=dict, blank=True)

    last_webhook_received_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.ghl_call_id


class GHLCallTranscriptBulkEdit(GHLCall):
    class Meta:
        proxy = True
        verbose_name = "Transcript Bulk Edit"
        verbose_name_plural = "Transcript Bulk Edit"


class PromptSpec(models.Model):
    name = models.CharField(max_length=255, blank=True)
    prompt = models.TextField()
    is_active = models.BooleanField(default=False, db_index=True)
    score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    response_time = models.FloatField(null=True, blank=True)
    token_cost = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.name.strip():
            self.name = self.prompt.strip()[:80]
        super().save(*args, **kwargs)
        if self.is_active:
            PromptSpec.objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)

    def __str__(self) -> str:
        return self.name or self.prompt[:80]


class UnifiedNodeQuestion(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class UnifiedNodeAnswer(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class UnifiedNodeStatement(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class BaseUnifiedNodeAlias(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.name = " ".join((self.name or "").split()).strip()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class UnifiedNodeQuestionAlias(BaseUnifiedNodeAlias):
    unified_question = models.ForeignKey(
        UnifiedNodeQuestion,
        on_delete=models.CASCADE,
        related_name="aliases",
    )


class UnifiedNodeAnswerAlias(BaseUnifiedNodeAlias):
    unified_answer = models.ForeignKey(
        UnifiedNodeAnswer,
        on_delete=models.CASCADE,
        related_name="aliases",
    )


class UnifiedNodeStatementAlias(BaseUnifiedNodeAlias):
    unified_statement = models.ForeignKey(
        UnifiedNodeStatement,
        on_delete=models.CASCADE,
        related_name="aliases",
    )


class BaseCallSegment(models.Model):
    speaker_role = models.CharField(
        max_length=20,
        choices=GHLCall.SpeakerRole.choices,
        default=GHLCall.SpeakerRole.UNKNOWN,
    )
    text = models.TextField(blank=True)
    ai_accuracy_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    human_accuracy_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    start_index = models.PositiveIntegerField(null=True, blank=True)
    end_index = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["created_at", "id"]


class Question(BaseCallSegment):
    call = models.ForeignKey(
        GHLCall,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    unified_question = models.ForeignKey(
        UnifiedNodeQuestion,
        on_delete=models.CASCADE,
        related_name="questions",
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return self.text[:80] or f"Question {self.pk}"


class Answer(BaseCallSegment):
    call = models.ForeignKey(
        GHLCall,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        "ghl_calls.Question",
        on_delete=models.CASCADE,
        related_name="answers",
        null=True,
        blank=True,
    )
    unified_answer = models.ForeignKey(
        UnifiedNodeAnswer,
        on_delete=models.CASCADE,
        related_name="answers",
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return self.text[:80] or f"Answer {self.pk}"


class Statement(BaseCallSegment):
    call = models.ForeignKey(
        GHLCall,
        on_delete=models.CASCADE,
        related_name="statements",
    )
    unified_statement = models.ForeignKey(
        UnifiedNodeStatement,
        on_delete=models.CASCADE,
        related_name="statements",
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return self.text[:80] or f"Statement {self.pk}"


class QuestionGroupingReview(Question):
    class Meta:
        proxy = True
        verbose_name = "Question Grouping Review"
        verbose_name_plural = "Question Grouping Review"


class CallNote(models.Model):
    class EditOption(models.TextChoices):
        CHANGE = "CHG", "Change / Replace"
        DELETE = "DEL", "Delete / Remove"
        ADD = "ADD", "Add / Missing"
        MOVE = "MOV", "Reorder / Move"
        GOOD = "OK", "Perfect as is"

    call = models.ForeignKey(
        GHLCall,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    start_index = models.PositiveIntegerField(null=True, blank=True)
    end_index = models.PositiveIntegerField(null=True, blank=True)
    edit_option = models.CharField(
        max_length=3,
        choices=EditOption.choices,
        default=EditOption.GOOD,
    )
    negative_impact_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-100), MaxValueValidator(100)],
    )
    original_text = models.TextField(blank=True)
    replacement_text = models.TextField(blank=True)
    note = models.TextField(blank=True)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="notes",
        null=True,
        blank=True,
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name="notes",
        null=True,
        blank=True,
    )
    statement = models.ForeignKey(
        Statement,
        on_delete=models.CASCADE,
        related_name="notes",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        if self.original_text or self.replacement_text:
            return f"{self.original_text[:30]} -> {self.replacement_text[:30]}".strip(" ->")
        return self.note[:80] or f"CallNote {self.pk}"


class GHLCallWebhookEvent(models.Model):
    event_type = models.CharField(max_length=128, db_index=True)
    event_id = models.CharField(max_length=128, blank=True, db_index=True)

    call = models.ForeignKey(
        GHLCall,
        on_delete=models.CASCADE,
        related_name="webhook_events",
        null=True,
        blank=True,
    )

    signature = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self) -> str:
        return self.event_type or f"Webhook event {self.pk}"
