import json
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connections
from django.utils import timezone


DEFAULT_MAIN_SOURCE = {
    "ENGINE": "django.db.backends.mysql",
    "NAME": "dbfightfire",
    "USER": "root",
    "PASSWORD": "",
    "HOST": "127.0.0.1",
    "PORT": "3307",
    "OPTIONS": {
        "charset": "utf8mb4",
    },
}

DEFAULT_SUB_SOURCE = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": "C:/Users/cyafei/programmingbiz/db.sqlite3",
}

# Main-project data stays in main-project tables.
MAIN_ENTITY_SPECS = [
    "auth.user",
    "core",
    "company",
    "attendance",
    "privser",
    "exchange",
    "synchronization",
    "paychex",
    "dispatch",
    "automations",
]

# Subproject data only goes into the copied subproject tables.
# Intentionally excludes:
# - auth/admin/contenttypes/sessions: shared Django internals
# - automations: schema conflicts with the main-project automations app
SUB_ENTITY_SPECS = [
    "checkin_pwa",
    "evernote_pwa",
    "companies",
    "contacts",
    "pic_pwa",
    "id_scanner",
    "jobs",
    "invoices",
    "integrations",
    "ghl_calls",
    "learndash",
    "learndash_webhook",
    "pdf_plugin",
]


class Command(BaseCommand):
    help = (
        "Export main-project data from MySQL and subproject data from SQLite, "
        "then optionally load both into the current target database while keeping "
        "their tables separate."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dump",
            action="store_true",
            help="Write JSON fixtures for the configured main and sub sources.",
        )
        parser.add_argument(
            "--load",
            action="store_true",
            help="Load the generated fixtures into the target database alias.",
        )
        parser.add_argument(
            "--allow-nonempty-target",
            action="store_true",
            help="Allow loading into a target database that already has rows in imported tables.",
        )
        parser.add_argument(
            "--skip-main",
            action="store_true",
            help="Skip the main-project source.",
        )
        parser.add_argument(
            "--skip-sub",
            action="store_true",
            help="Skip the subproject source.",
        )
        parser.add_argument(
            "--output-dir",
            default="merge_fixtures",
            help="Directory where generated fixtures will be written.",
        )
        parser.add_argument(
            "--target",
            default="default",
            help="Target database alias to load into. Defaults to Django's default database.",
        )

    def handle(self, *args, **options):
        if options["skip_main"] and options["skip_sub"]:
            raise CommandError("Nothing to do: both --skip-main and --skip-sub were passed.")

        output_dir = Path(options["output_dir"]).resolve()
        target_alias = options["target"]

        source_configs = {}
        if not options["skip_main"]:
            source_configs["source_main"] = self._build_source_config(
                prefix="MERGE_MAIN_DB",
                default_config=DEFAULT_MAIN_SOURCE,
            )
        if not options["skip_sub"]:
            source_configs["source_sub"] = self._build_source_config(
                prefix="MERGE_SUB_DB",
                default_config=DEFAULT_SUB_SOURCE,
            )

        for alias, config in source_configs.items():
            self._register_database(alias, config)
            self._test_connection(alias)

        main_models = []
        main_dump_specs = []
        if "source_main" in source_configs:
            main_models = self._filter_models_for_alias(
                "source_main",
                self._resolve_models(MAIN_ENTITY_SPECS),
            )
            main_dump_specs = self._model_specs(main_models)

        sub_models = []
        sub_dump_specs = []
        if "source_sub" in source_configs:
            sub_models = self._filter_models_for_alias(
                "source_sub",
                self._resolve_models(SUB_ENTITY_SPECS),
            )
            sub_dump_specs = self._model_specs(sub_models)

        self.stdout.write(self.style.NOTICE("Source summary"))
        if "source_main" in source_configs:
            self._print_counts("source_main", "Main project", main_models)
        if "source_sub" in source_configs:
            self._print_counts("source_sub", "Subproject", sub_models)

        if not options["dump"] and not options["load"]:
            self.stdout.write(
                self.style.SUCCESS(
                    "Inspection complete. Re-run with --dump to create fixtures or --dump --load to import them."
                )
            )
            return

        output_dir.mkdir(parents=True, exist_ok=True)
        fixture_paths = {}

        if options["dump"]:
            timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
            if "source_main" in source_configs:
                fixture_paths["main"] = output_dir / f"main_project_{timestamp}.json"
                self._dump_fixture("source_main", main_dump_specs, fixture_paths["main"])
                self._rewrite_main_fixture(fixture_paths["main"])
            if "source_sub" in source_configs:
                fixture_paths["sub"] = output_dir / f"sub_project_{timestamp}.json"
                self._dump_fixture("source_sub", sub_dump_specs, fixture_paths["sub"])
                self._rewrite_sub_fixture(fixture_paths["sub"])

        if options["load"]:
            if not fixture_paths:
                raise CommandError("--load currently requires --dump in the same run.")
            target_models = []
            if "main" in fixture_paths:
                target_models.extend(main_models)
            if "sub" in fixture_paths:
                target_models.extend(sub_models)

            if not options["allow_nonempty_target"]:
                self._assert_target_is_empty(target_alias, target_models)

            if "main" in fixture_paths:
                self.stdout.write(self.style.NOTICE(f"Loading main fixture into '{target_alias}'"))
                call_command("loaddata", str(fixture_paths["main"]), database=target_alias)
            if "sub" in fixture_paths:
                self.stdout.write(self.style.NOTICE(f"Loading sub fixture into '{target_alias}'"))
                call_command("loaddata", str(fixture_paths["sub"]), database=target_alias)

            self._reset_sequences(target_alias, target_models)
            self.stdout.write(
                self.style.SUCCESS(
                    "Separated project data loaded successfully. Main and subproject tables remain independent."
                )
            )

    def _build_source_config(self, prefix, default_config):
        config = connections.databases["default"].copy()
        engine = self._env(f"{prefix}_ENGINE", default_config.get("ENGINE"))
        name = self._env(f"{prefix}_NAME", default_config.get("NAME"))
        if not engine or not name:
            raise CommandError(f"Missing required source database settings for prefix {prefix}.")

        engine = self._normalize_engine(engine)
        config["ENGINE"] = engine
        config["NAME"] = name

        if engine == "django.db.backends.sqlite3":
            config["USER"] = ""
            config["PASSWORD"] = ""
            config["HOST"] = ""
            config["PORT"] = ""
            config.setdefault("OPTIONS", {})
            return config

        config["USER"] = self._env(f"{prefix}_USER", default_config.get("USER", ""))
        config["PASSWORD"] = self._env(f"{prefix}_PASSWORD", default_config.get("PASSWORD", ""), allow_blank=True)
        config["HOST"] = self._env(f"{prefix}_HOST", default_config.get("HOST", "127.0.0.1"))
        config["PORT"] = self._env(f"{prefix}_PORT", default_config.get("PORT", ""))

        if default_config.get("OPTIONS"):
            config["OPTIONS"] = default_config["OPTIONS"]

        return config

    def _env(self, key, default=None, allow_blank=False):
        import os

        if key in os.environ:
            value = os.environ.get(key)
            if allow_blank or value not in (None, ""):
                return value
            return default
        return default

    def _normalize_engine(self, engine):
        value = str(engine).strip().lower()
        if value in {"mysql", "django.db.backends.mysql"}:
            return "django.db.backends.mysql"
        if value in {"postgres", "postgresql", "django.db.backends.postgresql"}:
            return "django.db.backends.postgresql"
        if value in {"sqlite", "sqlite3", "django.db.backends.sqlite3"}:
            return "django.db.backends.sqlite3"
        raise CommandError(f"Unsupported database engine: {engine}")

    def _register_database(self, alias, config):
        settings.DATABASES[alias] = config
        connections.databases[alias] = config

    def _test_connection(self, alias):
        try:
            connection = connections[alias]
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            self.stdout.write(self.style.SUCCESS(f"Connected to {alias}"))
        except Exception as exc:
            raise CommandError(f"Could not connect to {alias}: {exc}") from exc

    def _resolve_models(self, specs):
        resolved = []
        seen = set()
        for spec in specs:
            if "." in spec:
                app_label, model_name = spec.split(".", 1)
                model = apps.get_model(app_label, model_name)
                key = (model._meta.app_label, model._meta.model_name)
                if key not in seen:
                    resolved.append(model)
                    seen.add(key)
                continue

            app_config = apps.get_app_config(spec)
            for model in app_config.get_models():
                key = (model._meta.app_label, model._meta.model_name)
                if key not in seen:
                    resolved.append(model)
                    seen.add(key)

        return resolved

    def _print_counts(self, alias, label, models):
        self.stdout.write(self.style.NOTICE(f"{label} ({alias})"))
        for model in models:
            count = model._default_manager.using(alias).count()
            if count:
                self.stdout.write(f"  {model._meta.label}: {count}")

    def _filter_models_for_alias(self, alias, models):
        connection = connections[alias]
        existing_tables = set(connection.introspection.table_names())
        filtered = []
        for model in models:
            if model._meta.proxy:
                continue
            if model._meta.db_table in existing_tables:
                filtered.append(model)
        return filtered

    def _model_specs(self, models):
        return [f"{model._meta.app_label}.{model._meta.model_name}" for model in models]

    def _dump_fixture(self, alias, entity_specs, output_path):
        self.stdout.write(self.style.NOTICE(f"Dumping {alias} to {output_path}"))
        call_command(
            "dumpdata",
            *entity_specs,
            database=alias,
            indent=2,
            output=str(output_path),
        )

    def _rewrite_main_fixture(self, path):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload:
            if item["model"] == "auth.user":
                fields = item["fields"]
                fields.pop("groups", None)
                fields.pop("user_permissions", None)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _rewrite_sub_fixture(self, path):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload:
            if item["model"] == "pdf_plugin.pdfrenderlog":
                item["fields"]["user"] = None
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _assert_target_is_empty(self, alias, models):
        non_empty = []
        for model in models:
            count = model._default_manager.using(alias).count()
            if count:
                non_empty.append(f"{model._meta.label}={count}")

        if non_empty:
            raise CommandError(
                "Target database already contains imported rows. "
                "Use a fresh target DB or pass --allow-nonempty-target if this is intentional. "
                f"Found: {', '.join(non_empty[:10])}"
            )

    def _reset_sequences(self, alias, models):
        connection = connections[alias]
        statements = connection.ops.sequence_reset_sql(no_style(), models)
        if not statements:
            return

        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
