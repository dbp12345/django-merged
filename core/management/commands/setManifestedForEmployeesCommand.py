from django.core.management.base import BaseCommand

from core.tasks import set_manifested_status_tasks


# python manage.py setManifestedForEmployeesCommand
class Command(BaseCommand):
    help = "Run setManifestedForEmployeesCommand"

    def handle(self, *args, **options):
        set_manifested_status_tasks.apply_async()
        self.stdout.write(self.style.SUCCESS("setManifestedForEmployeesCommand done.") + "\n")
