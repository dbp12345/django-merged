"""
Automation engine for executing automation actions.

This module contains functions to execute automation actions
based on their configuration (code execution or webhook calls).
"""

import logging
from datetime import date, datetime

import requests
from django.db import models
from .models import AutomationLog

logger = logging.getLogger(__name__)


def execute_automation(automation, instance, old_value=None, new_value=None):
    """
    Main execution function for automations.

    Args:
        automation: Automation instance to execute
        instance: Model instance that triggered the automation
        old_value: Previous value of the field (for field_changed triggers)
        new_value: New value of the field (for field_changed triggers)

    Returns:
        AutomationLog instance with execution results
    """
    success = False
    error_message = ""

    # Get model label for logging
    if instance:
        model_label = f"{instance._meta.app_label}.{instance._meta.object_name}"
    else:
        model_label = automation.trigger_model

    try:
        if automation.action_type == "code":
            execute_code(automation, instance, old_value, new_value)
            success = True
        elif automation.action_type == "webhook":
            execute_webhook(automation, instance, old_value, new_value)
            success = True
        else:
            error_message = f"Unknown action type: {automation.action_type}"

    except Exception as e:
        error_message = str(e)
        logger.error(
            f"Error executing automation {automation.name}: {error_message}",
            exc_info=True,
        )

    # Log execution result
    log_entry = AutomationLog.objects.create(
        automation=automation,
        success=success,
        error_message=error_message,
        object_id=instance.pk if instance else 0,
        model_label=model_label,
    )

    return log_entry


def execute_code(automation, instance, old_value, new_value):
    """
    Execute user's Python code for the automation.

    Creates a namespace with useful variables and executes the code.
    After execution, saves the instance if it exists and hasn't been deleted.

    Args:
        automation: Automation instance
        instance: Model instance that triggered the automation
        old_value: Previous value of the field
        new_value: New value of the field

    Raises:
        Exception: Any exception raised by the user's code
    """
    if not instance:
        raise ValueError("Instance is required for code execution")

    # Create namespace with available variables
    namespace = {
        "instance": instance,
        "old_value": old_value,
        "new_value": new_value,
        "date": date,
        "datetime": datetime,
        "models": models,
    }

    # Execute user's code
    exec(automation.action_code, namespace)

    # After execution, if instance was modified, call instance.save()
    # Check if instance still exists in database before saving
    if instance.pk:
        try:
            # Verify instance still exists in database
            instance.__class__.objects.get(pk=instance.pk)
            instance.save()
        except instance.__class__.DoesNotExist:
            # Instance was deleted, don't try to save
            logger.warning(
                f"Instance {instance.__class__.__name__}(pk={instance.pk}) was deleted, skipping save"
            )
        except Exception as e:
            # Other save errors, log but don't fail the automation
            logger.warning(f"Error saving instance after automation: {e}")


def execute_webhook(automation, instance, old_value, new_value):
    """
    Send POST request to webhook URL with trigger information.

    Args:
        automation: Automation instance
        instance: Model instance that triggered the automation
        old_value: Previous value of the field
        new_value: New value of the field

    Raises:
        requests.RequestException: If webhook request fails
    """
    if not automation.webhook_url:
        raise ValueError("Webhook URL is required for webhook action type")

    # Prepare payload with generic structure
    payload = {
        "automation_name": automation.name,
        "trigger_field": automation.trigger_field,
        "old_value": str(old_value) if old_value else None,
        "new_value": str(new_value) if new_value else None,
        "object_id": instance.pk if instance else None,
        "model": f"{instance._meta.app_label}.{instance._meta.object_name}" if instance else None,
    }

    # Send POST request
    response = requests.post(
        automation.webhook_url,
        json=payload,
        timeout=30,
        headers={"Content-Type": "application/json"},
    )

    # Raise exception if request failed
    response.raise_for_status()
