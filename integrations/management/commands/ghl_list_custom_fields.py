# integrations/management/commands/ghl_list_custom_fields.py
from django.core.management.base import BaseCommand

from integrations.models import GHLAuth
from integrations.ghl_client import request


class Command(BaseCommand):
    help = "List GoHighLevel (LeadConnector) custom fields for the connected location"

    def handle(self, *args, **options):
        auth = GHLAuth.objects.first()
        if not auth or not auth.location_id:
            raise SystemExit("Missing GHLAuth.location_id. Complete OAuth at /oauth/start/.")

        location_id = auth.location_id

        data = request(
            "GET",
            f"/locations/{location_id}/customFields",
            include_location_id=False,  # IMPORTANT: already in URL
        )

        fields = data.get("customFields") or data.get("custom_fields") or data
        self.stdout.write(self.style.SUCCESS(f"Fetched custom fields for location {location_id}"))
        self.stdout.write(str(fields))
