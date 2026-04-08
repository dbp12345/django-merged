import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import NoteForm
from .models import EvernoteConnection, Notebook, Note
from .services import (
    EvernoteConfigurationError,
    complete_authorization,
    create_authorization,
    is_configured,
    pull_remote_state,
    push_pending_notes,
)


def _create_local_notebook_from_request(request):
    notebook_name = (request.POST.get("notebook_name") or "").strip()
    if not notebook_name:
        messages.error(request, "Notebook name cannot be empty.")
        return None

    notebook = Notebook.objects.create(
        guid=f"local-{uuid.uuid4()}",
        name=notebook_name,
        is_active=True,
    )
    messages.success(request, f'Notebook "{notebook.name}" created.')
    return notebook


@login_required(login_url="/admin/login/")
def dashboard(request):
    if request.method == "POST":
        notebook = _create_local_notebook_from_request(request)
        if notebook:
            return redirect(f'{reverse("evernote_pwa:dashboard")}?notebook={notebook.pk}')
        return redirect("evernote_pwa:dashboard")

    connection = EvernoteConnection.get_solo()
    context = {
        "connection": connection,
        "is_configured": is_configured(),
        "note_count": Note.objects.count(),
        "notebook_count": Notebook.objects.count(),
        "pushable_count": Note.objects.filter(needs_push=True, allow_push_to_evernote=True).count(),
    }
    return render(request, "evernote_pwa/dashboard.html", context)


@login_required(login_url="/admin/login/")
def notebooks_page(request):
    if request.method == "POST":
        notebook = _create_local_notebook_from_request(request)
        if notebook:
            return redirect(f'{reverse("evernote_pwa:notebooks")}?notebook={notebook.pk}')
        return redirect("evernote_pwa:notebooks")

    notebook_id = request.GET.get("notebook")
    notebooks = Notebook.objects.prefetch_related("notes").all()
    selected_notebook = None
    notes = Note.objects.select_related("notebook").all()

    if notebook_id and notebook_id.isdigit():
        selected_notebook = get_object_or_404(Notebook, pk=int(notebook_id))
        notes = notes.filter(notebook=selected_notebook)

    return render(
        request,
        "evernote_pwa/notebooks.html",
        {
            "notebooks": notebooks,
            "selected_notebook": selected_notebook,
            "notes": notes,
        },
    )


@login_required(login_url="/admin/login/")
def notes_page(request):
    notes = Note.objects.select_related("notebook").all()
    notebooks = Notebook.objects.all()
    return render(
        request,
        "evernote_pwa/notes.html",
        {
            "notes": notes,
            "notebooks": notebooks,
            "note_count": notes.count(),
        },
    )


@login_required(login_url="/admin/login/")
def note_create(request):
    if request.method == "POST":
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.source = Note.SOURCE_LOCAL
            note.allow_push_to_evernote = False
            note.needs_push = False
            note.save()
            messages.success(request, "Local note saved.")
            return redirect("evernote_pwa:notes")
    else:
        initial = {}
        notebook_id = request.GET.get("notebook")
        if notebook_id and notebook_id.isdigit():
            initial["notebook"] = notebook_id
        form = NoteForm(initial=initial)

    return render(
        request,
        "evernote_pwa/note_form.html",
        {"form": form, "page_title": "New note", "note": None},
    )


@login_required(login_url="/admin/login/")
def note_edit(request, pk: int):
    note = get_object_or_404(Note.objects.select_related("notebook"), pk=pk)
    if request.method == "POST":
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            note = form.save(commit=False)
            note.mark_dirty_for_push()
            note.save()
            if note.can_push_to_evernote:
                messages.success(request, "Note saved locally and marked for push to Evernote.")
            else:
                messages.success(request, "Note saved locally.")
            return redirect(reverse("evernote_pwa:note_edit", args=[note.pk]))
    else:
        form = NoteForm(instance=note)

    return render(
        request,
        "evernote_pwa/note_form.html",
        {"form": form, "page_title": "Edit note", "note": note},
    )


@login_required(login_url="/admin/login/")
def oauth_start(request):
    if not is_configured():
        messages.error(
            request,
            "Set EVERNOTE_CONSUMER_KEY and EVERNOTE_CONSUMER_SECRET in the environment first.",
        )
        return redirect("evernote_pwa:dashboard")

    callback_url = request.build_absolute_uri(reverse("evernote_pwa:oauth_callback"))
    try:
        authorize_url = create_authorization(request, callback_url)
    except EvernoteConfigurationError as exc:
        messages.error(request, str(exc))
        return redirect("evernote_pwa:dashboard")

    return redirect(authorize_url)


@login_required(login_url="/admin/login/")
def oauth_callback(request):
    oauth_verifier = (request.GET.get("oauth_verifier") or "").strip()
    if not oauth_verifier:
        return HttpResponseBadRequest("Missing oauth_verifier")

    try:
        complete_authorization(request, oauth_verifier)
    except EvernoteConfigurationError as exc:
        messages.error(request, str(exc))
        return redirect("evernote_pwa:dashboard")

    messages.success(request, "Evernote connected.")
    return redirect("evernote_pwa:dashboard")


@login_required(login_url="/admin/login/")
@require_http_methods(["POST"])
def sync_pull(request):
    try:
        summary = pull_remote_state()
    except EvernoteConfigurationError as exc:
        messages.error(request, str(exc))
        return redirect("evernote_pwa:dashboard")

    messages.success(
        request,
        f"Pulled {summary.pulled_notes} notes across {summary.notebooks} notebooks.",
    )
    return redirect("evernote_pwa:dashboard")


@login_required(login_url="/admin/login/")
@require_http_methods(["POST"])
def sync_push(request):
    try:
        summary = push_pending_notes()
    except EvernoteConfigurationError as exc:
        messages.error(request, str(exc))
        return redirect("evernote_pwa:dashboard")

    messages.success(request, f"Pushed {summary.pushed_notes} note updates to Evernote.")
    return redirect("evernote_pwa:dashboard")
