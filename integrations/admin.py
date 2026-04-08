from django.contrib import admin

from .models import GHLAuth, GHLContactSyncMeta, GHLSyncState


@admin.register(GHLAuth)
class GHLAuthAdmin(admin.ModelAdmin):
    list_display = ("location_id", "sync_mode", "expires_at", "updated_at")
    search_fields = ("location_id",)
    list_filter = ("sync_mode", "updated_at")


@admin.register(GHLSyncState)
class GHLSyncStateAdmin(admin.ModelAdmin):
    list_display = ("id", "last_push_at", "last_pull_at", "last_run_at", "updated_at")


@admin.register(GHLContactSyncMeta)
class GHLContactSyncMetaAdmin(admin.ModelAdmin):
    list_display = ("contact", "last_synced_at", "ghl_last_modified_at", "updated_at")
    search_fields = ("contact__email", "contact__first_name", "contact__last_name")
