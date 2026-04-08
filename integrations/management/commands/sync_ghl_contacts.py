# integrations/management/commands/sync_ghl_contacts.py
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from integrations.ghl_sync import pull_ghl_to_django, push_django_to_ghl
from integrations.models import GHLSyncState


class Command(BaseCommand):
    help = "2-way sync: GHL <-> Django (email primary, Django id stored in custom field, prefer Django only on dual-change conflict)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Do not write to DB.")
        parser.add_argument("--page-limit", type=int, default=100)
        parser.add_argument("--max-pages", type=int, default=500)

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        page_limit = int(options["page_limit"])
        max_pages = int(options["max_pages"])

        state, _ = GHLSyncState.objects.get_or_create(id=1)

        now = timezone.now()
        changed_since = state.last_pull_at  # best-effort global filter

        self.stdout.write(self.style.NOTICE("--- Starting 2-way sync (poll + push) ---"))

        pull_res = pull_ghl_to_django(
            page_limit=page_limit,
            max_pages=max_pages,
            changed_since=changed_since,
            dry_run=dry_run,
        )

        push_res = push_django_to_ghl()

        if not dry_run:
            state.last_pull_at = now
            state.last_push_at = now
            state.last_run_at = now
            state.save(update_fields=["last_pull_at", "last_push_at", "last_run_at", "updated_at"])

        self.stdout.write(
            self.style.SUCCESS(
                "--- Sync complete "
                f"(pull_created={pull_res.created}, pull_updated={pull_res.updated}, "
                f"linked={pull_res.linked}, conflicts_pref_django={pull_res.conflicts_pref_django}, skipped={pull_res.skipped}; "
                f"push_pushed={push_res.pushed}, push_created={push_res.created}, relinked={push_res.relinked}, push_skipped={push_res.skipped}) ---"
            )
        )
