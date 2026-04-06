"""
Dynamic admin inline configuration system.
Allows configuring inline fields and readonly_fields via Django admin UI.
"""

import json
import logging
from django.db import models
from django.contrib import admin
from django.utils.html import format_html

logger = logging.getLogger(__name__)


class AdminInlineConfig(models.Model):
    """
    Store configuration for admin inlines.
    Allows dynamic field configuration without code changes.
    """

    inline_class_name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Exact class name of the inline (e.g., 'FireRunInline')",
    )
    fields_config = models.JSONField(
        default=list,
        blank=True,
        help_text="List of field names to display. Example: ['field1', 'field2']",
    )
    readonly_fields_config = models.JSONField(
        default=list,
        blank=True,
        help_text="List of readonly field names. Example: ['field1', 'field2']",
    )
    notes = models.TextField(
        blank=True, help_text="Optional notes about this configuration"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Admin Inline Configuration"
        verbose_name_plural = "Admin Inline Configurations"
        ordering = ["inline_class_name"]

    def __str__(self):
        return f"{self.inline_class_name} ({len(self.fields_config)} fields)"


class ConfigurableInlineMixin:
    """
    Mixin for admin inlines to load configuration from AdminInlineConfig.

    Usage:
        class YourInline(ConfigurableInlineMixin, admin.TabularInline):
            model = YourModel
            fields = ['default', 'fields']  # Used as fallback
            readonly_fields = ['default', 'readonly']  # Used as fallback
    """

    def get_fields(self, request, obj=None):
        """
        Override get_fields to load configuration from AdminInlineConfig.
        Falls back to class-level 'fields' attribute if no config exists.
        """
        try:
            config = AdminInlineConfig.objects.get(
                inline_class_name=self.__class__.__name__
            )
            if config.fields_config:
                logger.debug(
                    f"Using configured fields for {self.__class__.__name__}: "
                    f"{len(config.fields_config)} fields"
                )
                return tuple(config.fields_config)
        except AdminInlineConfig.DoesNotExist:
            logger.debug(
                f"No config found for {self.__class__.__name__}, using default fields"
            )
        except Exception as e:
            logger.error(
                f"Failed to load config for {self.__class__.__name__}: {e}",
                exc_info=True,
            )

        # Fallback to default fields (from class definition)
        # Try super() first, then fallback to class attribute
        try:
            result = super().get_fields(request, obj)
            if result is not None:
                return result
        except AttributeError:
            pass

        # Fallback to class-level fields attribute
        return getattr(self, 'fields', ())

    def get_readonly_fields(self, request, obj=None):
        """
        Override get_readonly_fields to load configuration from AdminInlineConfig.
        Falls back to class-level 'readonly_fields' attribute if no config exists.
        """
        try:
            config = AdminInlineConfig.objects.get(
                inline_class_name=self.__class__.__name__
            )
            if config.readonly_fields_config:
                logger.debug(
                    f"Using configured readonly_fields for {self.__class__.__name__}: "
                    f"{len(config.readonly_fields_config)} fields"
                )
                return tuple(config.readonly_fields_config)
        except AdminInlineConfig.DoesNotExist:
            logger.debug(
                f"No config found for {self.__class__.__name__}, using default readonly_fields"
            )
        except Exception as e:
            logger.error(
                f"Failed to load config for {self.__class__.__name__}: {e}",
                exc_info=True,
            )

        # Fallback to default readonly_fields (from class definition)
        # Try super() first, then fallback to class attribute
        try:
            result = super().get_readonly_fields(request, obj)
            if result is not None:
                return result
        except AttributeError:
            pass

        # Fallback to class-level readonly_fields attribute
        return getattr(self, 'readonly_fields', ())


@admin.register(AdminInlineConfig)
class AdminInlineConfigAdmin(admin.ModelAdmin):
    """Admin interface for managing inline configurations."""

    list_display = ["inline_class_name", "fields_count", "readonly_count", "updated_at"]

    list_filter = ["updated_at"]

    search_fields = ["inline_class_name", "notes"]

    fields = [
        "inline_class_name",
        "available_fields_help",
        "fields_config",
        "readonly_fields_config",
        "notes",
    ]

    readonly_fields = ["available_fields_help", "updated_at"]

    def available_fields_help(self, obj):
        """Show available fields for the selected inline class."""
        if not obj or not obj.inline_class_name:
            return format_html(
                '<p style="color: #666;">Save the record first to see available fields</p>'
            )

        # Get inline class
        inline_class = self._get_inline_class(obj.inline_class_name)
        if not inline_class:
            return format_html(
                '<p style="color: #d00;">Inline class "{}" not found. '
                "Make sure the class name is correct.</p>",
                obj.inline_class_name,
            )

        # Get model fields
        try:
            model = inline_class.model
            model_fields = [f.name for f in model._meta.get_fields()]

            # Get custom display methods from inline
            custom_methods = [
                name
                for name in dir(inline_class)
                if not name.startswith("_")
                and callable(getattr(inline_class, name))
                and hasattr(getattr(inline_class, name), "short_description")
            ]

            all_fields = sorted(model_fields + custom_methods)

            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; '
                'border-radius: 4px; font-family: monospace;">'
                "<p><strong>Available fields (copy and paste into JSON):</strong></p>"
                '<pre style="margin: 0;">{}</pre>'
                "</div>",
                json.dumps(all_fields, indent=2),
            )
        except Exception as e:
            return format_html(
                '<p style="color: #d00;">Error getting fields: {}</p>', str(e)
            )

    available_fields_help.short_description = "Available fields"

    def _get_inline_class(self, class_name):
        """
        Dynamically get inline class by name.
        Searches in common admin modules and registered admin classes.
        """
        # First, try to search all registered admin modules
        try:
            from django.contrib import admin
            # Search through all registered ModelAdmin classes
            for model, admin_class in admin.site._registry.items():
                # Check if this admin has inlines
                if hasattr(admin_class, "inlines"):
                    for inline in admin_class.inlines:
                        if inline.__name__ == class_name:
                            return inline
        except Exception as e:
            logger.debug(f"Failed to search registered admins for {class_name}: {e}")

        # If not found, try common admin modules
        admin_modules = [
            "core.admin_panel.admin.EmployeesAdmin",
            "core.admin_panel.admin.FireRunAdmin",
            "core.admin_panel.admin.CrewAdmin",
        ]

        for module_path in admin_modules:
            try:
                # Import module dynamically (e.g., "core.admin_panel.admin.EmployeesAdmin")
                parts = module_path.split(".")
                module_name = ".".join(parts[:-1])  # "core.admin_panel.admin"
                class_name_in_module = parts[-1]  # "EmployeesAdmin"
                module = __import__(module_name, fromlist=[class_name_in_module])
                # Now search for the inline class in this module
                inline_class = getattr(module, class_name, None)
                if inline_class:
                    return inline_class
            except (ImportError, AttributeError) as e:
                logger.debug(f"Failed to import from {module_path}: {e}")
                continue

        logger.warning(f"Inline class '{class_name}' not found in any admin module")
        return None

    def fields_count(self, obj):
        """Display number of configured fields."""
        return len(obj.fields_config) if obj.fields_config else 0

    fields_count.short_description = "Fields"

    def readonly_count(self, obj):
        """Display number of readonly fields."""
        return len(obj.readonly_fields_config) if obj.readonly_fields_config else 0

    readonly_count.short_description = "Readonly"

    class Media:
        css = {"all": ("admin/css/forms.css",)}
