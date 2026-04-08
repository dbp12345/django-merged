from django.contrib import admin

from .models import EvernoteConnection, Notebook, Note


@admin.register(EvernoteConnection)
class EvernoteConnectionAdmin(admin.ModelAdmin):
    list_display = ("username", "connected_at", "last_pulled_at", "last_pushed_at")


@admin.register(Notebook)
class NotebookAdmin(admin.ModelAdmin):
    list_display = ("name", "stack", "is_default", "is_active", "updated_at")
    search_fields = ("name", "stack", "guid")
    list_filter = ("is_default", "is_active")


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("title", "notebook", "source", "needs_push", "is_deleted_remote", "updated_at")
    search_fields = ("title", "evernote_guid", "content")
    list_filter = ("source", "needs_push", "allow_push_to_evernote", "is_deleted_remote")

