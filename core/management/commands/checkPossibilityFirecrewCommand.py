from django.conf import settings
from django.core.management.base import BaseCommand

from company.models import Employees
from core.tasks import check_possibility_firecrew_task


class Command(BaseCommand):
    help = "checkPossibilityFirecrewCommand"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(f"Run checkPossibilityFirecrewCommand."))

        employees_on_firecrews = Employees.objects.filter(fire_crew__isnull=False)

        count = 0
        for obj in employees_on_firecrews:
            if settings.DEBUG:
                check_possibility_firecrew_task.run(employee_id=obj.id)
            else:
                check_possibility_firecrew_task.delay(employee_id=obj.id)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"{count} checked."))
