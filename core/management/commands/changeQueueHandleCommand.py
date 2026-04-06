from django.core.management.base import BaseCommand
from core.services.ChangedParametersService import ChangedParametersService

# python manage.py changeQueueHandleCommand
class Command(BaseCommand):
    help = "Run changeQueueHandleCommand"

    def handle(self, *args, **options):
        ChangedParametersService.send_grouped_changes()