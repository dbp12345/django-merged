from django.conf import settings
from django.db import models


class PDFTemplate(models.Model):
    name = models.SlugField(max_length=200, unique=True, help_text="Unique identifier for this template")
    version = models.PositiveIntegerField(default=1, help_text="Template version number")
    enabled = models.BooleanField(default=True, help_text="Whether this template is active")
    root_model_label = models.CharField(
        max_length=200,
        help_text="Dotted path to root model (e.g. 'company.Employee')",
    )
    template_file = models.FileField(
        upload_to="pdf_plugin/templates/",
        help_text="The fillable PDF template file",
    )
    output_filename_pattern = models.CharField(
        max_length=255,
        default="{template.name}_{root.pk}_{now:%Y%m%d_%H%M%S}.pdf",
        help_text="Python format string for output filename. Available: template, root, now",
    )
    flatten = models.BooleanField(
        default=False,
        help_text=(
            "WARNING: Flatten may remove visual appearance of filled values. "
            "Currently, flatten is disabled as it requires explicit appearance stream generation. "
            "Keep this unchecked to preserve filled form fields."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "version")
        unique_together = [["name", "version"]]
        verbose_name = "PDF Template"
        verbose_name_plural = "PDF Templates"

    def __str__(self):
        return f"{self.name} v{self.version}"


class PDFFieldMap(models.Model):
    template = models.ForeignKey(PDFTemplate, on_delete=models.CASCADE, related_name="field_maps")
    enabled = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    pdf_field_name = models.CharField(
        max_length=200,
        help_text="Exact name of the PDF AcroForm field",
    )
    value_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Dotted path to value (e.g. 'company.name' or 'first_name')",
    )
    default_value = models.CharField(
        max_length=500,
        blank=True,
        help_text="Default value if value_path is empty or fails",
    )

    class Meta:
        ordering = ("template", "order", "pdf_field_name")
        verbose_name = "PDF Field Mapping"
        verbose_name_plural = "PDF Field Mappings"

    def __str__(self):
        return f"{self.template.name}: {self.pdf_field_name} → {self.value_path or self.default_value}"


class PDFRenderLog(models.Model):
    template = models.ForeignKey(
        "PDFTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    template_name = models.CharField(max_length=200, blank=True)  # fallback if template deleted
    template_version = models.PositiveIntegerField(default=0)

    root_model_label = models.CharField(max_length=200)
    root_pk = models.CharField(max_length=64)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "PDF Render Log"
        verbose_name_plural = "PDF Render Logs"

    def __str__(self):
        return f"{self.created_at} {self.root_model_label}:{self.root_pk} {self.template_name} v{self.template_version}"
