from __future__ import annotations

import sys
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import connections
from django.utils.text import slugify

from pdf_plugin.engine import PDFFormEngine
from pdf_plugin.models import PDFFieldMap, PDFTemplate
from pdf_plugin.services import render_pdf_for_instance


class Command(BaseCommand):
    help = "Guided installer for pdf_plugin (safe to run multiple times)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\nPDF Plugin Installer\n"))

        self._check_environment()
        self._check_database()

        if not PDFTemplate.objects.exists():
            self._maybe_create_first_template()
        else:
            self.stdout.write(
                self.style.SUCCESS("✓ PDF templates already exist — skipping creation.")
            )

        self.stdout.write(self.style.SUCCESS("\nPDF Plugin installation complete.\n"))
        self.stdout.write("Next steps:")
        self.stdout.write("• Admin → PDF Plugin → PDF Templates")
        self.stdout.write("• Optional: enable /pdf/ URLs")
        self.stdout.write("• Optional: add PDFGenerateMixin to your ModelAdmin\n")

    # ------------------------------------------------------------------

    def _check_environment(self):
        self.stdout.write("Checking environment…")

        # Django version
        import django

        if django.VERSION < (5, 0):
            self.stderr.write("✗ Django 5.x required")
            sys.exit(1)
        self.stdout.write(f"✓ Django {django.get_version()}")

        # MEDIA_ROOT
        if not getattr(settings, "MEDIA_ROOT", None):
            self.stderr.write("✗ MEDIA_ROOT is not configured in settings.py")
            sys.exit(1)

        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)
        self.stdout.write(f"✓ MEDIA_ROOT = {media_root}")

        # pypdf
        try:
            import pypdf  # noqa

            self.stdout.write("✓ pypdf installed")
        except ImportError:
            self.stderr.write("✗ pypdf not installed. Run: pip install pypdf")
            sys.exit(1)

    # ------------------------------------------------------------------

    def _check_database(self):
        self.stdout.write("\nChecking database…")

        conn = connections["default"]
        if not conn.introspection.table_names():
            self.stderr.write("✗ Database not initialized. Run migrations first.")
            sys.exit(1)

        self.stdout.write("✓ Database reachable")

    # ------------------------------------------------------------------

    def _maybe_create_first_template(self):
        answer = input("\nNo PDF templates found. Create one now? [Y/n]: ").strip().lower()
        if answer not in ("", "y", "yes"):
            return

        # Step 1: Choose model
        model = self._select_model()

        # Step 2: Template name
        name = input("\nTemplate name (e.g. Employee Taskbook): ").strip()
        slug = slugify(name)

        # Step 3: PDF file
        pdf_path = Path(input("Path to fillable PDF file: ").strip()).expanduser()
        if not pdf_path.exists():
            self.stderr.write("✗ PDF file not found.")
            sys.exit(1)

        # Step 4: Create template record
        data = pdf_path.read_bytes()
        tpl = PDFTemplate.objects.create(
            name=slug,
            version=1,
            enabled=True,
            root_model_label=f"{model._meta.app_label}.{model.__name__}",
        )
        tpl.template_file.save(pdf_path.name, ContentFile(data), save=True)

        self.stdout.write(self.style.SUCCESS(f"✓ Created template '{tpl.name}'"))

        # Step 5: Discover fields
        from django.core.files.storage import default_storage
        try:
            template_path = Path(default_storage.path(tpl.template_file.name))
        except (NotImplementedError, AttributeError):
            # For remote storage, use the file directly
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tpl.template_file.seek(0)
                tmp.write(tpl.template_file.read())
                template_path = Path(tmp.name)

        answer = input(
            "Discover PDF form fields and create placeholders? [Y/n]: "
        ).strip().lower()
        if answer in ("", "y", "yes"):
            self._create_placeholder_fields(tpl, template_path)

        # Step 6: Smoke test
        self._smoke_test(tpl, model)

    # ------------------------------------------------------------------

    def _select_model(self):
        self.stdout.write("\nSelect root model:")

        models = [
            m
            for m in apps.get_models()
            if not m._meta.abstract and not m._meta.proxy
        ]

        for idx, m in enumerate(models, start=1):
            self.stdout.write(f"{idx:>3}) {m._meta.app_label}.{m.__name__}")

        choice = int(input("\nEnter number: ").strip())
        return models[choice - 1]

    # ------------------------------------------------------------------

    def _create_placeholder_fields(self, template, pdf_path):
        fields = PDFFormEngine.list_fields(pdf_path)
        if not fields:
            self.stdout.write("⚠ No AcroForm fields found.")
            return

        for order, field in enumerate(fields):
            PDFFieldMap.objects.create(
                template=template,
                enabled=True,
                order=order,
                pdf_field_name=field,
                value_path="",
                default_value="",
            )

        self.stdout.write(
            self.style.SUCCESS(f"✓ Created {len(fields)} placeholder field mappings")
        )

    # ------------------------------------------------------------------

    def _smoke_test(self, template, model):
        answer = input("\nRun smoke test render now? [Y/n]: ").strip().lower()
        if answer not in ("", "y", "yes"):
            return

        pk = input(f"Enter primary key of {model.__name__}: ").strip()
        obj = model.objects.get(pk=pk)

        result = render_pdf_for_instance(template, obj)

        out = Path.cwd() / f"{template.name}_test.pdf"
        out.write_bytes(result.pdf_bytes)

        self.stdout.write(
            self.style.SUCCESS(f"✓ Test PDF written to {out}")
        )
