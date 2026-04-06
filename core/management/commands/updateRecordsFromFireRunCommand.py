from django.core.management.base import BaseCommand
from core.services.RecordsService import RecordsService


# python manage.py updateRecordsFromFireRunCommand
class Command(BaseCommand):
    help = "Run updateRecordsFromFireRunCommand"

    def handle(self, *args, **options):
        RecordsService.set_operational_periods_for_all_employees()
        self.stdout.write(self.style.SUCCESS("updateRecordsFromFireRunCommand done.\n"))
