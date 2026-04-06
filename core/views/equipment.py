from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from dispatch.models.Equipment import EquipmentType, Equipment


def _build_schema_from_equipment_type(equipment_type, obj=None):
    """Build JSON schema based on equipment type parameters"""
    if not equipment_type:
        return {"type": "object", "keys": {}}

    schema = {"type": "object", "keys": {}}

    # Build schema from equipment type parameters
    if equipment_type.parameters_schema:
        for param in equipment_type.parameters_schema:
            param_name = param.get("name")
            if not param_name:
                continue

            # Get field type and validate it
            field_type = param.get("field_type", "string")

            # Auto-detect select type if choices are provided
            choices = param.get("choices", [])
            if choices and isinstance(choices, list) and len(choices) > 0:
                # If choices are provided, automatically set as select
                field_type = "select"

            # Validate field type
            if not field_type or field_type not in ["string", "number", "boolean", "select", "date"]:
                field_type = "string"  # default to string if invalid

            # Map field types to valid JSON schema types
            # django-jsonform expects: string, number, boolean, array, object
            json_schema_type = "string"  # default
            if field_type == "number":
                json_schema_type = "number"
            elif field_type == "boolean":
                json_schema_type = "boolean"
            elif field_type == "date":
                json_schema_type = "string"  # dates are strings in JSON
            elif field_type == "select":
                json_schema_type = "string"  # select is string with choices

            field_schema = {
                "title": param_name,
                "type": json_schema_type,
            }

            # Unit of measurement in help_text
            if param.get("unit"):
                field_schema["help_text"] = f"Единица измерения: {param['unit']}"

            # Required field
            if param.get("required"):
                field_schema["required"] = True

            # Choices for select
            if field_type == "select" and choices and len(choices) > 0:
                field_schema["choices"] = choices

            # Date format for date fields
            if field_type == "date":
                field_schema["format"] = "date"

            schema["keys"][param_name] = field_schema

    # If editing existing object, also include any keys from existing data
    # that might not be in the schema (legacy data handling)
    if obj and obj.parameters:
        existing_keys = set(obj.parameters.keys())
        schema_keys = set(schema["keys"].keys())
        missing_keys = existing_keys - schema_keys

        # Add missing keys as string fields to prevent validation errors
        for key in missing_keys:
            if key and key not in schema["keys"]:
                schema["keys"][key] = {
                    "title": key,
                    "type": "string",
                }

    return schema


@require_http_methods(["GET"])
def get_equipment_type_schema(request, equipment_type_id):
    """Get JSON schema for equipment type parameters"""
    equipment_type = get_object_or_404(EquipmentType, pk=equipment_type_id)
    
    # Get equipment object if editing
    equipment_obj = None
    equipment_id = request.GET.get("equipment_id")
    if equipment_id:
        try:
            equipment_obj = Equipment.objects.get(pk=equipment_id)
        except Equipment.DoesNotExist:
            pass
    
    schema = _build_schema_from_equipment_type(equipment_type, obj=equipment_obj)
    
    return JsonResponse({
        "status": "success",
        "schema": schema,
        "equipment_type_id": equipment_type_id,
        "equipment_type_name": equipment_type.name,
    })

