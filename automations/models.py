from django.db import models
from django.core.validators import URLValidator


class Automation(models.Model):
    """
    Model for storing automation configurations.
    Users can create trigger-based automations through the admin interface.
    """

    TRIGGER_TYPE_CHOICES = [
        ("field_changed", "Field Changed"),
        ("created", "Created"),
        ("deleted", "Deleted"),
    ]

    ACTION_TYPE_CHOICES = [
        ("code", "Execute Python Code"),
        ("webhook", "POST to Webhook URL"),
    ]

    name = models.CharField(max_length=200, help_text="Name of the automation")
    is_active = models.BooleanField(
        default=True, help_text="Enable or disable this automation"
    )
    trigger_model = models.CharField(
        max_length=100,
        help_text="Enter as 'app_label.ModelName' (e.g., 'company.Employees', 'company.Company', 'dispatch.Dispatch')",
    )
    trigger_field = models.CharField(
        max_length=100,
        help_text="Enter exact field name from the model",
        blank=True,
    )
    trigger_type = models.CharField(
        max_length=20,
        choices=TRIGGER_TYPE_CHOICES,
        help_text="Type of trigger event",
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPE_CHOICES,
        help_text="Type of action to execute",
    )
    action_code = models.TextField(
        blank=True,
        help_text="Python code with access to: instance, old_value, new_value, date, datetime, models",
    )
    webhook_url = models.URLField(
        blank=True,
        help_text="Webhook URL for POST requests",
        validators=[URLValidator()],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Automation"
        verbose_name_plural = "Automations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.trigger_model})"

    def clean(self):
        """
        Validate that action_code is provided for 'code' action_type
        and webhook_url is provided for 'webhook' action_type.
        """
        from django.core.exceptions import ValidationError

        if self.action_type == "code" and not self.action_code:
            raise ValidationError(
                {"action_code": "Action code is required when action type is 'code'."}
            )
        if self.action_type == "webhook" and not self.webhook_url:
            raise ValidationError(
                {
                    "webhook_url": "Webhook URL is required when action type is 'webhook'."
                }
            )
        if self.trigger_type == "field_changed" and not self.trigger_field:
            raise ValidationError(
                {
                    "trigger_field": "Trigger field is required when trigger type is 'field_changed'."
                }
            )


class AutomationLog(models.Model):
    """
    Model for logging automation executions.
    Stores execution results for debugging and auditing.
    """

    automation = models.ForeignKey(
        Automation, on_delete=models.CASCADE, related_name="logs"
    )
    executed_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(help_text="Whether the automation executed successfully")
    error_message = models.TextField(
        blank=True, help_text="Error message if execution failed"
    )
    object_id = models.IntegerField(
        help_text="ID of the object that triggered the automation"
    )
    model_label = models.CharField(
        max_length=100,
        help_text="Which model triggered this automation",
        default="",
    )

    class Meta:
        verbose_name = "Automation Log"
        verbose_name_plural = "Automation Logs"
        ordering = ["-executed_at"]

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.automation.name} - {status} - {self.executed_at}"
