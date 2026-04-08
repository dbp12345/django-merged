from django.db import models
from django.utils import timezone


class EvernoteConnection(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    access_token = models.TextField(blank=True)
    username = models.CharField(max_length=255, blank=True)
    edam_user_id = models.BigIntegerField(null=True, blank=True)
    shard_id = models.CharField(max_length=64, blank=True)
    connected_at = models.DateTimeField(null=True, blank=True)
    last_pulled_at = models.DateTimeField(null=True, blank=True)
    last_pushed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evernote connection"
        verbose_name_plural = "Evernote connection"

    def __str__(self) -> str:
        return self.username or "Evernote connection"

    @property
    def is_connected(self) -> bool:
        return bool(self.access_token)

    @classmethod
    def get_solo(cls) -> "EvernoteConnection":
        return cls.objects.get_or_create(id=1)[0]


class Notebook(models.Model):
    guid = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    stack = models.CharField(max_length=255, blank=True)
    update_sequence_num = models.BigIntegerField(default=0)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_seen_remote_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self) -> str:
        return self.name


class Note(models.Model):
    SOURCE_IMPORTED = "imported"
    SOURCE_LOCAL = "local"
    SOURCE_CHOICES = (
        (SOURCE_IMPORTED, "Imported"),
        (SOURCE_LOCAL, "Local"),
    )

    notebook = models.ForeignKey(
        Notebook,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notes",
    )
    evernote_guid = models.CharField(max_length=64, unique=True, null=True, blank=True)
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    content_enml = models.TextField(blank=True)
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES, default=SOURCE_LOCAL)
    allow_push_to_evernote = models.BooleanField(default=False)
    needs_push = models.BooleanField(default=False)
    is_deleted_remote = models.BooleanField(default=False)
    remote_created_at = models.DateTimeField(null=True, blank=True)
    remote_updated_at = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title", "-updated_at", "id"]

    def __str__(self) -> str:
        return self.title or f"Note {self.pk}"

    @property
    def can_push_to_evernote(self) -> bool:
        return bool(self.allow_push_to_evernote and self.evernote_guid)

    def mark_dirty_for_push(self) -> None:
        if self.can_push_to_evernote:
            self.needs_push = True

    def mark_synced(self, when=None) -> None:
        when = when or timezone.now()
        self.last_synced_at = when
        self.needs_push = False

