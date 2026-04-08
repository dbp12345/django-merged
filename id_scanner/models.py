from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from contacts.models import Contact


class IDScanGroup(models.Model):
    THRESHOLD_ADAPTIVE = "adaptive"
    THRESHOLD_OTSU = "otsu"
    THRESHOLD_CHOICES = (
        (THRESHOLD_ADAPTIVE, "Adaptive"),
        (THRESHOLD_OTSU, "Otsu"),
    )

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    grayscale_enabled = models.BooleanField(default=True)
    upscale_enabled = models.BooleanField(default=True)
    deskew_enabled = models.BooleanField(default=True)
    binarize_enabled = models.BooleanField(default=True)
    noise_removal_enabled = models.BooleanField(default=True)
    isolate_roi_enabled = models.BooleanField(default=True)
    optimize_ocr_enabled = models.BooleanField(default=True)
    apply_psm_enabled = models.BooleanField(default=True)
    apply_whitelist_enabled = models.BooleanField(default=True)
    post_process_enabled = models.BooleanField(default=True)
    data_validation_enabled = models.BooleanField(default=True)
    remove_background_enabled = models.BooleanField(default=True)
    level_perspective_enabled = models.BooleanField(default=True)

    scale_factor = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.75,
        validators=[MinValueValidator(1), MaxValueValidator(4)],
    )
    default_psm = models.PositiveSmallIntegerField(default=6)
    default_whitelist = models.CharField(max_length=255, blank=True)
    threshold_mode = models.CharField(
        max_length=20,
        choices=THRESHOLD_CHOICES,
        default=THRESHOLD_ADAPTIVE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        verbose_name = "ID scan group"
        verbose_name_plural = "ID scan groups"

    def __str__(self) -> str:
        return self.name

    @property
    def enabled_steps(self) -> list[str]:
        steps = []
        if self.grayscale_enabled:
            steps.append("Grayscale")
        if self.upscale_enabled:
            steps.append("Upscale")
        if self.deskew_enabled:
            steps.append("Deskew")
        if self.binarize_enabled:
            steps.append("Binarize")
        if self.noise_removal_enabled:
            steps.append("Noise removal")
        if self.isolate_roi_enabled:
            steps.append("ROI")
        if self.optimize_ocr_enabled:
            steps.append("Optimized OCR")
        if self.post_process_enabled:
            steps.append("Post-process")
        if self.data_validation_enabled:
            steps.append("Validation")
        if self.remove_background_enabled:
            steps.append("Background removal")
        if self.level_perspective_enabled:
            steps.append("Perspective leveling")
        return steps


class IDScanTemplate(models.Model):
    DOCUMENT_DRIVER_LICENSE = "driver_license"
    DOCUMENT_STATE_ID = "state_id"
    DOCUMENT_PERMIT = "permit"
    DOCUMENT_PASSPORT = "passport"
    DOCUMENT_OTHER = "other"
    DOCUMENT_CHOICES = (
        (DOCUMENT_DRIVER_LICENSE, "Driver license"),
        (DOCUMENT_STATE_ID, "State ID"),
        (DOCUMENT_PERMIT, "Permit"),
        (DOCUMENT_PASSPORT, "Passport"),
        (DOCUMENT_OTHER, "Other"),
    )

    group = models.ForeignKey(
        IDScanGroup,
        on_delete=models.CASCADE,
        related_name="templates",
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)
    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_CHOICES,
        default=DOCUMENT_DRIVER_LICENSE,
    )
    issuer_region = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    target_width = models.PositiveIntegerField(default=1000)
    target_height = models.PositiveIntegerField(default=630)
    accepted_date_input_formats = models.CharField(
        max_length=255,
        default="%m/%d/%Y,%m-%d-%Y,%m %d %Y,%m%d%Y",
        help_text="Comma-separated Python strptime formats for DOB/expiry normalization.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["group__name", "name", "id"]
        unique_together = (("group", "slug"),)
        verbose_name = "ID scan template"
        verbose_name_plural = "ID scan templates"

    def __str__(self) -> str:
        return f"{self.group.name} / {self.name}"


class IDScanField(models.Model):
    FIELD_FULL_NAME = "full_name"
    FIELD_DOB = "dob"
    FIELD_ID_NUMBER = "id_number"
    FIELD_EXPIRY = "expiry"
    FIELD_ADDRESS = "address"
    FIELD_CUSTOM = "custom"
    FIELD_CHOICES = (
        (FIELD_FULL_NAME, "Full name"),
        (FIELD_DOB, "Date of birth"),
        (FIELD_ID_NUMBER, "ID number"),
        (FIELD_EXPIRY, "Expiry"),
        (FIELD_ADDRESS, "Address"),
        (FIELD_CUSTOM, "Custom"),
    )

    template = models.ForeignKey(
        IDScanTemplate,
        on_delete=models.CASCADE,
        related_name="fields",
    )
    key = models.SlugField(max_length=50)
    label = models.CharField(max_length=120)
    field_type = models.CharField(
        max_length=20,
        choices=FIELD_CHOICES,
        default=FIELD_CUSTOM,
    )
    roi_left = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    roi_top = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    roi_width = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(0.0001), MaxValueValidator(1)],
    )
    roi_height = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(0.0001), MaxValueValidator(1)],
    )
    psm = models.PositiveSmallIntegerField(blank=True, null=True)
    whitelist = models.CharField(max_length=255, blank=True)
    validation_regex = models.CharField(max_length=255, blank=True)
    expected_length = models.PositiveSmallIntegerField(blank=True, null=True)
    required = models.BooleanField(default=False)
    normalize_whitespace = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        unique_together = (("template", "key"),)
        verbose_name = "ID scan field"
        verbose_name_plural = "ID scan fields"

    def __str__(self) -> str:
        return f"{self.template.name} / {self.label}"


class IDScanRecord(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_ERROR, "Error"),
    )

    group = models.ForeignKey(
        IDScanGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scan_records",
    )
    template = models.ForeignKey(
        IDScanTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scan_records",
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="id_scan_records",
    )
    source_image = models.ImageField(upload_to="id_scanner/source/")
    warped_image = models.ImageField(upload_to="id_scanner/warped/", blank=True)
    processed_image = models.ImageField(upload_to="id_scanner/processed/", blank=True)
    raw_ocr_text = models.JSONField(default=dict, blank=True)
    extracted_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    error_message = models.TextField(blank=True)
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "ID scan record"
        verbose_name_plural = "ID scan records"

    def __str__(self) -> str:
        template_name = self.template.name if self.template_id else "No template"
        return f"Scan #{self.pk} ({template_name})"
