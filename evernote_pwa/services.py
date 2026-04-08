from __future__ import annotations

import html
import os
import re
from dataclasses import dataclass
from datetime import timezone as dt_timezone

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import EvernoteConnection, Notebook, Note


SESSION_REQUEST_TOKEN_KEY = "evernote_request_token"
SESSION_REQUEST_SECRET_KEY = "evernote_request_secret"


class EvernoteConfigurationError(RuntimeError):
    pass


@dataclass
class SyncSummary:
    notebooks: int = 0
    pulled_notes: int = 0
    pushed_notes: int = 0


def get_consumer_key() -> str:
    return getattr(settings, "EVERNOTE_CONSUMER_KEY", os.environ.get("EVERNOTE_CONSUMER_KEY", "")).strip()


def get_consumer_secret() -> str:
    return getattr(
        settings,
        "EVERNOTE_CONSUMER_SECRET",
        os.environ.get("EVERNOTE_CONSUMER_SECRET", ""),
    ).strip()


def get_service_host() -> str:
    return getattr(
        settings,
        "EVERNOTE_SERVICE_HOST",
        os.environ.get("EVERNOTE_SERVICE_HOST", "www.evernote.com"),
    ).strip() or "www.evernote.com"


def use_sandbox() -> bool:
    raw = getattr(settings, "EVERNOTE_SANDBOX", os.environ.get("EVERNOTE_SANDBOX", "0"))
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def is_configured() -> bool:
    return bool(get_consumer_key() and get_consumer_secret())


def _require_sdk():
    try:
        from evernote.api.client import EvernoteClient
        from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
        from evernote.edam.type.ttypes import Note as EdamNote
    except ModuleNotFoundError as exc:
        raise EvernoteConfigurationError(
            "Evernote SDK is not installed. Install requirements before connecting."
        ) from exc

    return EvernoteClient, NoteFilter, NotesMetadataResultSpec, EdamNote


def _oauth_client():
    if not is_configured():
        raise EvernoteConfigurationError(
            "Set EVERNOTE_CONSUMER_KEY and EVERNOTE_CONSUMER_SECRET before connecting."
        )

    EvernoteClient, _, _, _ = _require_sdk()
    return EvernoteClient(
        consumer_key=get_consumer_key(),
        consumer_secret=get_consumer_secret(),
        sandbox=use_sandbox(),
        service_host=get_service_host(),
    )


def _token_client(access_token: str):
    EvernoteClient, _, _, _ = _require_sdk()
    return EvernoteClient(
        token=access_token,
        sandbox=use_sandbox(),
        service_host=get_service_host(),
    )


def create_authorization(request, callback_url: str) -> str:
    client = _oauth_client()
    token = client.get_request_token(callback_url)
    request.session[SESSION_REQUEST_TOKEN_KEY] = token["oauth_token"]
    request.session[SESSION_REQUEST_SECRET_KEY] = token["oauth_token_secret"]
    return client.get_authorize_url(token)


def complete_authorization(request, oauth_verifier: str) -> EvernoteConnection:
    oauth_token = request.session.get(SESSION_REQUEST_TOKEN_KEY, "")
    oauth_secret = request.session.get(SESSION_REQUEST_SECRET_KEY, "")
    if not oauth_token or not oauth_secret:
        raise EvernoteConfigurationError("Missing Evernote request token in session. Start connect again.")

    client = _oauth_client()
    access_token = client.get_access_token(oauth_token, oauth_secret, oauth_verifier)
    auth_client = _token_client(access_token)
    user_store = auth_client.get_user_store()
    user = user_store.getUser()

    connection = EvernoteConnection.get_solo()
    connection.access_token = access_token
    connection.username = getattr(user, "username", "") or ""
    connection.edam_user_id = getattr(user, "id", None)
    connection.shard_id = getattr(user, "shardId", "") or ""
    connection.connected_at = timezone.now()
    connection.save()

    request.session.pop(SESSION_REQUEST_TOKEN_KEY, None)
    request.session.pop(SESSION_REQUEST_SECRET_KEY, None)
    return connection


def _get_note_store(connection: EvernoteConnection):
    if not connection.access_token:
        raise EvernoteConfigurationError("Evernote is not connected yet.")

    client = _token_client(connection.access_token)
    return client.get_note_store()


def _from_en_timestamp(value):
    if not value:
        return None
    return timezone.datetime.fromtimestamp(value / 1000, tz=dt_timezone.utc)


def _strip_enml(content_enml: str) -> str:
    text = re.sub(r"<\?xml.*?\?>", "", content_enml or "", flags=re.DOTALL)
    text = re.sub(r"<!DOCTYPE.*?>", "", text, flags=re.DOTALL)
    text = re.sub(r"<en-note[^>]*>", "", text, flags=re.DOTALL)
    text = re.sub(r"</en-note>", "", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _to_enml(content: str) -> str:
    lines = (content or "").splitlines() or [""]
    body = "".join(f"<div>{html.escape(line) or '<br/>'}</div>" for line in lines)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
        f"<en-note>{body}</en-note>"
    )


@transaction.atomic
def pull_remote_state() -> SyncSummary:
    connection = EvernoteConnection.get_solo()
    note_store = _get_note_store(connection)
    _, NoteFilter, NotesMetadataResultSpec, _ = _require_sdk()

    summary = SyncSummary()
    now = timezone.now()
    seen_notebooks = set()
    seen_notes = set()

    remote_notebooks = note_store.listNotebooks(connection.access_token)
    for remote_notebook in remote_notebooks:
        seen_notebooks.add(remote_notebook.guid)
        notebook, _ = Notebook.objects.update_or_create(
            guid=remote_notebook.guid,
            defaults={
                "name": remote_notebook.name,
                "stack": getattr(remote_notebook, "stack", "") or "",
                "update_sequence_num": getattr(remote_notebook, "updateSequenceNum", 0) or 0,
                "is_default": bool(getattr(remote_notebook, "defaultNotebook", False)),
                "is_active": True,
                "last_seen_remote_at": now,
            },
        )
        summary.notebooks += 1

        note_filter = NoteFilter(notebookGuid=remote_notebook.guid)
        result_spec = NotesMetadataResultSpec(
            includeTitle=True,
            includeUpdated=True,
            includeCreated=True,
            includeNotebookGuid=True,
        )
        offset = 0
        page_size = 50

        while True:
            result = note_store.findNotesMetadata(
                connection.access_token,
                note_filter,
                offset,
                page_size,
                result_spec,
            )
            notes = getattr(result, "notes", []) or []
            if not notes:
                break

            for metadata in notes:
                full_note = note_store.getNote(
                    connection.access_token,
                    metadata.guid,
                    True,
                    False,
                    False,
                    False,
                )
                seen_notes.add(metadata.guid)
                note, created = Note.objects.get_or_create(
                    evernote_guid=metadata.guid,
                    defaults={
                        "source": Note.SOURCE_IMPORTED,
                        "allow_push_to_evernote": True,
                    },
                )
                note.notebook = notebook
                note.title = getattr(metadata, "title", "") or "Untitled"
                note.content_enml = getattr(full_note, "content", "") or ""
                note.content = _strip_enml(note.content_enml)
                note.source = Note.SOURCE_IMPORTED
                if created:
                    note.allow_push_to_evernote = True
                note.is_deleted_remote = False
                note.remote_created_at = _from_en_timestamp(getattr(metadata, "created", None))
                note.remote_updated_at = _from_en_timestamp(getattr(metadata, "updated", None))
                note.mark_synced(now)
                note.save()
                summary.pulled_notes += 1

            offset += len(notes)
            if offset >= getattr(result, "totalNotes", 0):
                break

    if seen_notebooks:
        Notebook.objects.exclude(guid__in=seen_notebooks).update(is_active=False)

    Note.objects.filter(source=Note.SOURCE_IMPORTED).exclude(
        evernote_guid__in=seen_notes or [""]
    ).update(is_deleted_remote=True)

    connection.last_pulled_at = now
    connection.save(update_fields=["last_pulled_at", "updated_at"])
    return summary


@transaction.atomic
def push_pending_notes() -> SyncSummary:
    connection = EvernoteConnection.get_solo()
    note_store = _get_note_store(connection)
    _, _, _, EdamNote = _require_sdk()

    summary = SyncSummary()
    now = timezone.now()

    pending_notes = Note.objects.select_related("notebook").filter(
        needs_push=True,
        allow_push_to_evernote=True,
        evernote_guid__isnull=False,
    ).exclude(evernote_guid="")

    for note in pending_notes:
        remote_note = EdamNote()
        remote_note.guid = note.evernote_guid
        remote_note.title = note.title or "Untitled"
        remote_note.content = _to_enml(note.content)
        if note.notebook and note.notebook.guid:
            remote_note.notebookGuid = note.notebook.guid

        updated = note_store.updateNote(connection.access_token, remote_note)
        note.content_enml = remote_note.content
        note.remote_updated_at = _from_en_timestamp(getattr(updated, "updated", None)) or now
        note.mark_synced(now)
        note.save(update_fields=["content_enml", "remote_updated_at", "last_synced_at", "needs_push", "updated_at"])
        summary.pushed_notes += 1

    connection.last_pushed_at = now
    connection.save(update_fields=["last_pushed_at", "updated_at"])
    return summary
