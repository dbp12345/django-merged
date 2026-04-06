from django.contrib import admin
from django_jsonform.widgets import JSONFormWidget

from dispatch.models.Equipment import EquipmentType, Equipment


@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "equipment_count"]
    search_fields = ["name", "description"]

    def equipment_count(self, obj):
        return obj.equipment.count()

    equipment_count.short_description = "Number of units"


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ["name", "equipment_type", "serial_number", "installation_date"]
    list_filter = ["equipment_type", "factories", "installation_date"]
    search_fields = ["name", "serial_number", "notes"]
    filter_horizontal = ["factories"]
    date_hierarchy = "installation_date"

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "serial_number",
                    "equipment_type",
                    "installation_date",
                )
            },
        ),
        (
            "Parameters",
            {
                "fields": ("parameters",),
                "description": "Parameters depend on the selected equipment type",
            },
        ),
        ("Factory Assignment", {"fields": ("factories",)}),
        ("Additional Information", {"fields": ("notes",), "classes": ("collapse",)}),
    )

    def get_form(self, request, obj=None, **kwargs):
        """Override get_form to ensure schema is set correctly"""
        form = super().get_form(request, obj, **kwargs)

        # If we have an object, equipment_type is already set
        # If creating new, we need to check POST data or form initial data
        equipment_type = None

        if obj:
            equipment_type = obj.equipment_type
        elif request.method == "POST":
            # Check POST data for equipment_type
            equipment_type_id = request.POST.get("equipment_type")
            if equipment_type_id:
                try:
                    equipment_type = EquipmentType.objects.get(pk=equipment_type_id)
                except EquipmentType.DoesNotExist:
                    pass

        # Update parameters field widget schema if needed
        if "parameters" in form.base_fields:
            if equipment_type:
                schema = self._build_schema_from_equipment_type(equipment_type, obj=obj)
            else:
                # Empty schema - must have at least "keys" or "properties"
                schema = {
                    "type": "object",
                    "keys": {},
                    "title": "Select equipment type first, then save the form",
                }
            form.base_fields["parameters"].widget = JSONFormWidget(schema=schema)

        return form

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Dynamically update schema for parameters field based on equipment_type"""
        if db_field.name == "parameters":
            # Get equipment ID from URL (if editing existing equipment)
            obj_id = request.resolver_match.kwargs.get("object_id")
            equipment_type = None
            equipment_obj = None

            if obj_id:
                # Editing existing equipment
                try:
                    equipment_obj = Equipment.objects.get(pk=obj_id)
                    equipment_type = equipment_obj.equipment_type
                except Equipment.DoesNotExist:
                    pass
            else:
                # Creating new equipment - check POST data for equipment_type
                if request.method == "POST":
                    equipment_type_id = request.POST.get("equipment_type")
                    if equipment_type_id:
                        try:
                            equipment_type = EquipmentType.objects.get(
                                pk=equipment_type_id
                            )
                        except EquipmentType.DoesNotExist:
                            pass

            # Build schema based on equipment_type
            if equipment_type:
                schema = self._build_schema_from_equipment_type(
                    equipment_type, obj=equipment_obj
                )
            else:
                # Empty schema - must have at least "keys" or "properties"
                schema = {
                    "type": "object",
                    "keys": {},
                    "title": "Select equipment type first, then save the form",
                }

            kwargs["widget"] = JSONFormWidget(schema=schema)

        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def _build_schema_from_equipment_type(self, equipment_type, obj=None):
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
                if not field_type or field_type not in [
                    "string",
                    "number",
                    "boolean",
                    "select",
                    "date",
                ]:
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
                    field_schema["help_text"] = f"Unit of measurement: {param['unit']}"

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

    def save_model(self, request, obj, form, change):
        """Override save to clean parameters when equipment type changes"""
        if change and obj.pk:
            # Get the original object from database
            original_obj = Equipment.objects.get(pk=obj.pk)

            # If equipment type changed, clean parameters to match new schema
            if original_obj.equipment_type_id != obj.equipment_type_id:
                # Build new schema
                new_schema = self._build_schema_from_equipment_type(obj.equipment_type)
                new_schema_keys = set(new_schema.get("keys", {}).keys())

                # Filter parameters to keep only keys that exist in new schema
                if obj.parameters:
                    filtered_params = {}
                    for key, value in obj.parameters.items():
                        if key in new_schema_keys:
                            filtered_params[key] = value
                    obj.parameters = filtered_params
                else:
                    obj.parameters = {}

        super().save_model(request, obj, form, change)

    class Media:
        js = ("admin/js/equipment_admin.js",)


# Optional inline for displaying equipment on the factory page
class EquipmentInline(admin.TabularInline):
    model = Equipment.factories.through
    extra = 1
    verbose_name = "Equipment"
    verbose_name_plural = "Factory Equipment"
