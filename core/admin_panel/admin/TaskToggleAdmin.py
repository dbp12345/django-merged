from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from core.models.TaskToggle import Task_Toggle


@admin.register(Task_Toggle)
class TaskToggleAdmin(FlexListAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ("name", "is_enabled",)
    list_editable = ("is_enabled",)
    ordering = ("id",)
