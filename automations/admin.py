from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import ModelForm

from .models import Automation, AutomationLog


class AutomationForm(ModelForm):
    """
    Custom form for Automation model with validation.
    """

    class Meta:
        model = Automation
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        action_type = cleaned_data.get("action_type")
        action_code = cleaned_data.get("action_code")
        webhook_url = cleaned_data.get("webhook_url")
        trigger_type = cleaned_data.get("trigger_type")
        trigger_field = cleaned_data.get("trigger_field")

        # Validate action_type requirements
        if action_type == "code" and not action_code:
            raise ValidationError(
                {"action_code": "Action code is required when action type is 'code'."}
            )

        if action_type == "webhook" and not webhook_url:
            raise ValidationError(
                {
                    "webhook_url": "Webhook URL is required when action type is 'webhook'."
                }
            )

        # Validate trigger_type requirements
        if trigger_type == "field_changed" and not trigger_field:
            raise ValidationError(
                {
                    "trigger_field": "Trigger field is required when trigger type is 'field_changed'."
                }
            )

        return cleaned_data


@admin.register(Automation)
class AutomationAdmin(admin.ModelAdmin):
    """
    Admin interface for Automation model.
    """

    form = AutomationForm
    list_display = [
        "name",
        "trigger_model",
        "trigger_field",
        "trigger_type",
        "action_type",
        "is_active",
    ]
    list_filter = ["is_active", "trigger_type", "action_type"]
    search_fields = ["name", "trigger_model"]

    fieldsets = (
        (
            "Basic Info",
            {
                "fields": ("name", "is_active"),
            },
        ),
        (
            "Trigger Configuration",
            {
                "fields": ("trigger_model", "trigger_field", "trigger_type"),
            },
        ),
        (
            "Action Configuration",
            {
                "fields": ("action_type", "action_code", "webhook_url"),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")


@admin.register(AutomationLog)
class AutomationLogAdmin(admin.ModelAdmin):
    """
    Admin interface for AutomationLog model.
    All fields are readonly for auditing purposes.
    """

    list_display = ["automation", "model_label", "object_id", "executed_at", "success"]
    list_filter = ["success", "automation", "model_label"]
    search_fields = ["error_message", "model_label"]
    ordering = ["-executed_at"]
    readonly_fields = [
        "automation",
        "model_label",
        "executed_at",
        "success",
        "error_message",
        "object_id",
    ]

    fieldsets = (
        (
            "Execution Details",
            {
                "fields": ("automation", "model_label", "object_id", "executed_at", "success"),
            },
        ),
        (
            "Error Information",
            {
                "fields": ("error_message",),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        """Logs are created automatically, no manual creation allowed."""
        return False

    def has_change_permission(self, request, obj=None):
        """Logs are readonly, no editing allowed."""
        return False
