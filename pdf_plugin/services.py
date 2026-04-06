from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from django.core.files.storage import default_storage
from django.utils import timezone

from .engine import PDFFormEngine
from .models import PDFFieldMap, PDFRenderLog, PDFTemplate

logger = logging.getLogger(__name__)


@dataclass
class RenderResult:
    filename: str
    pdf_bytes: bytes
    field_values: dict


def resolve_value_path(value_path: str, root_instance: Any) -> str:
    """
    Resolve a dotted path like 'company.name' or 'first_name' from root_instance.
    Also supports function calls with parameters: 'get_param_value("surname")'
    Returns empty string if path cannot be resolved.
    """
    if not value_path:
        return ""

    import re

    # Check if path contains function call with parameter: function_name("param")
    func_call_match = re.match(r'^(\w+)\(["\']([^"\']+)["\']\)$', value_path.strip())
    if func_call_match:
        func_name = func_call_match.group(1)
        param_value = func_call_match.group(2)

        if hasattr(root_instance, func_name):
            func = getattr(root_instance, func_name)
            if callable(func):
                try:
                    result = func(param_value)
                    return "" if result is None else str(result)
                except Exception:
                    return ""
        return ""

    # Original dotted path logic
    parts = value_path.split(".")
    current = root_instance

    for part in parts:
        if hasattr(current, part):
            current = getattr(current, part)
        elif hasattr(current, "__getitem__"):
            try:
                current = current[part]
            except (KeyError, TypeError):
                return ""
        else:
            return ""

        # Handle callables (functions without parameters)
        if callable(current):
            try:
                current = current()
            except Exception:
                return ""

    # Convert to string, handling None
    return "" if current is None else str(current)


def render_pdf_for_instance(
    template: Union[str, int, PDFTemplate],
    root_instance: Any,
    *,
    user=None,
    ip_address: Optional[str] = None,
    user_agent: str = "",
) -> RenderResult:
    """
    Render a PDF for a given template and root instance.

    Args:
        template: PDFTemplate instance, name (str), or pk (int)
        root_instance: The Django model instance to use as root for value resolution
        user: Optional user for logging
        ip_address: Optional IP address for logging
        user_agent: Optional user agent string for logging

    Returns:
        RenderResult with filename, pdf_bytes, and field_values

    Raises:
        PDFTemplate.DoesNotExist: If template not found
        Exception: If PDF rendering fails
    """
    # Resolve template
    if isinstance(template, PDFTemplate):
        tpl = template
    elif isinstance(template, str):
        tpl = PDFTemplate.objects.get(name=template, enabled=True)
    elif isinstance(template, int):
        tpl = PDFTemplate.objects.get(pk=template, enabled=True)
    else:
        raise ValueError(f"Invalid template type: {type(template)}")

    # Validate root model
    app_label, model_name = tpl.root_model_label.split(".", 1)
    root_model = root_instance.__class__
    expected_label = f"{root_model._meta.app_label}.{root_model.__name__}"

    if tpl.root_model_label != expected_label:
        raise ValueError(
            f"Template root_model_label '{tpl.root_model_label}' does not match instance '{expected_label}'"
        )

    # Get template file path
    if not tpl.template_file:
        raise ValueError(f"Template '{tpl.name}' has no template_file")

    # Handle both local and remote storage
    try:
        template_path = Path(default_storage.path(tpl.template_file.name))
    except (NotImplementedError, AttributeError):
        # For remote storage (S3, etc.), download to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tpl.template_file.seek(0)
            tmp.write(tpl.template_file.read())
            template_path = Path(tmp.name)

    # Build field values from mappings
    field_values = {}
    mappings = PDFFieldMap.objects.filter(template=tpl, enabled=True).order_by("order")

    for mapping in mappings:
        value = ""
        if mapping.value_path:
            value = resolve_value_path(mapping.value_path, root_instance)
        if not value and mapping.default_value:
            value = mapping.default_value
        field_values[mapping.pdf_field_name] = value

    # Render PDF
    success = True
    error_message = ""

    try:
        engine = PDFFormEngine(template_path)
        # Always use flatten=False - proper flatten requires explicit appearance stream generation
        # which is complex in pypdf and may not preserve visual appearance of filled values
        pdf_bytes = engine.render(field_values, flatten=False)

        now = timezone.now()
        filename = tpl.output_filename_pattern.format(
            template=tpl, root=root_instance, now=now
        )

    except Exception as e:
        success = False
        error_message = str(e)
        logger.exception(f"PDF render failed: template={tpl.name} root={root_instance.pk}")
        raise
    finally:
        # Always log attempt
        try:
            PDFRenderLog.objects.create(
                template=tpl,
                template_name=tpl.name,
                template_version=tpl.version,
                root_model_label=tpl.root_model_label,
                root_pk=str(getattr(root_instance, "pk", "")),
                user=user,
                success=success,
                error_message=error_message,
                ip_address=ip_address,
                user_agent=user_agent or "",
            )
        except Exception:
            logger.exception("Failed to write PDFRenderLog")

    return RenderResult(filename=filename, pdf_bytes=pdf_bytes, field_values=field_values)
