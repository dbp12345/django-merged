# contacts/models.py
from __future__ import annotations

import io

import qrcode
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

from companies.models import Company


class Contact(models.Model):
    ROLE_CHOICES = [
        ("customer", "Customer"),
        ("employee", "Employee"),
        ("vendor", "Vendor"),
        ("other", "Other"),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    # ✅ Email is primary identity key for sync
    # Keep blank allowed if you need it, but enforce uniqueness when present (Meta constraint below)
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=50, blank=True)

    # ✅ Store GoHighLevel contact id here (linked record)
    privser_contact_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        help_text="GoHighLevel contact id (linked record)",
    )

    employee_record = models.FileField(
        upload_to="contacts/employee_records/",
        null=True,
        blank=True,
        help_text="Uploaded or generated employee record PDF.",
    )

    qr_code = models.ImageField(
        upload_to="contacts/qr_codes/",
        null=True,
        blank=True,
        help_text="Auto-generated QR code encoding this contact's ID.",
    )

    profile_picture = models.ImageField(
        upload_to="contacts/profile_pictures/",
        blank=True,
        null=True,
    )

    # ✅ check-in datetime
    check_in = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last check-in time (set by PWA QR scan).",
    )

    date = models.DateField(null=True, blank=True)
    text = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # ✅ needed for sync conflict detection

    class Meta:
        # Enforce "email is primary identity" in a safe way:
        # - allow blanks
        # - but if present, must be unique case-insensitively
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="uniq_contact_email_ci",
                condition=~Q(email="") & Q(email__isnull=False),
            )
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        """
        Save first to ensure PK exists, then generate QR on create (or if missing).

        NOTE: This will call save() twice:
          1) initial super().save()
          2) super().save(update_fields=["qr_code"])
        Our sync signal filters update_fields so this QR-only save won't push to GHL.
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Generate QR only if new OR missing
        if (is_new or not self.qr_code) and self.pk:
            img = qrcode.make(str(self.pk))

            buf = io.BytesIO()
            img.save(buf, format="PNG")

            filename = f"contact_{self.pk}.png"
            self.qr_code.save(
                filename,
                ContentFile(buf.getvalue()),
                save=False,
            )

            # Save only qr_code to avoid recursion
            super().save(update_fields=["qr_code"])
