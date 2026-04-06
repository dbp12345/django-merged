# Automation System - Quick Start Guide

## Overview

The automation system allows you to create trigger-based automations through the Django admin interface. Automations can execute Python code or send webhooks when model events occur.

## Creating an Automation

1. Go to **Admin Panel → Automations → Automations**
2. Click **Add Automation**
3. Fill in the fields:
   - **Name**: Descriptive name for the automation
   - **Is active**: Enable/disable the automation
   - **Trigger model**: Model to monitor (e.g., `company.Employees`)
   - **Trigger field**: Field to monitor (e.g., `status_code`)
   - **Trigger type**: 
     - `field_changed` - when field value changes
     - `created` - when new record is created
     - `deleted` - when record is deleted
   - **Action type**: 
     - `code` - execute Python code
     - `webhook` - POST to webhook URL

## Example: Execute Code on Field Change

**Trigger Model**: `company.Employees`  
**Trigger Field**: `status_code`  
**Trigger Type**: `field_changed`  
**Action Type**: `code`  
**Action Code**:
```python
# Update last modified time when status changes
from datetime import datetime
instance.last_modified_time = datetime.now()
```

## Example: Webhook on Record Creation

**Trigger Model**: `company.Employees`  
**Trigger Type**: `created`  
**Action Type**: `webhook`  
**Webhook URL**: `https://your-api.com/webhooks/new-employee`

## Available Variables in Code

When writing action code, these variables are available:
- `instance` - the model instance that triggered the automation
- `old_value` - previous value of the trigger field (None for new records)
- `new_value` - current value of the trigger field
- `date` - date module from datetime
- `datetime` - datetime module
- `models` - django.db.models module

## Viewing Execution Logs

All automation executions are logged in **Automations → Automation Logs**:
- View execution history
- Check success/failure status
- See error messages for debugging

## Performance Optimization

To improve performance, you can disable automations for specific models by editing `/app/automations/signals.py`:
- Remove models from `AUTOMATION_LISTEN_MODELS` list
- Comment out models you don't need to monitor
- Restart Django server after changes

## Important Notes

- Model names must be in format: `app_label.ModelName` (e.g., `company.Employees`)
- Field names must exactly match model field names
- After modifying code, restart Django server
- All code executions are logged for auditing
