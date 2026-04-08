from django.urls import path

from . import views

app_name = "evernote_pwa"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("notebooks/", views.notebooks_page, name="notebooks"),
    path("notes/", views.notes_page, name="notes"),
    path("connect/", views.oauth_start, name="oauth_start"),
    path("oauth/callback/", views.oauth_callback, name="oauth_callback"),
    path("sync/pull/", views.sync_pull, name="sync_pull"),
    path("sync/push/", views.sync_push, name="sync_push"),
    path("notes/new/", views.note_create, name="note_create"),
    path("notes/<int:pk>/", views.note_edit, name="note_edit"),
]
