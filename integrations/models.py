# integrations/models.py
from django.db import models
from django.utils import timezone


class GHLAuth(models.Model):
    class SyncMode(models.TextChoices):
        READ_WRITE = "read_write", "Read / Write"
        READ_ONLY = "read_only", "Read Only"

    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField(null=True, blank=True)

    location_id = models.CharField(max_length=64, null=True, blank=True, unique=True)
    sync_mode = models.CharField(
        max_length=20,
        choices=SyncMode.choices,
        default=SyncMode.READ_WRITE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        if not self.expires_at:
            return True
        return timezone.now() >= self.expires_at

    def is_read_only(self):
        return self.sync_mode == self.SyncMode.READ_ONLY

    def __str__(self):
        return self.location_id or f"GHLAuth {self.pk}"


class GHLSyncState(models.Model):
    """
    Single-row cursor for polling sync.
    """
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)

    last_push_at = models.DateTimeField(null=True, blank=True)
    last_pull_at = models.DateTimeField(null=True, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class GHLContactSyncMeta(models.Model):
    """
    Per-contact sync metadata (so we can do real 2-way sync + conflict detection).
    This lives in integrations app, so you don't have to modify contacts.Contact.
    """
    contact = models.OneToOneField(
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="ghl_sync_meta",
    )

    # Last time we successfully reconciled both systems for this contact
    last_synced_at = models.DateTimeField(null=True, blank=True)

    # Last GHL updatedAt we have seen for this contact (if GHL returns it)
    ghl_last_modified_at = models.DateTimeField(null=True, blank=True)

    # Hash of the fields we consider "synced fields"
    sync_hash = models.CharField(max_length=64, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
