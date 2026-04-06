from django.core.management.base import BaseCommand

from company.models import Employees
from company.signals.signals_for_DayOnFire import _sync_employee_last_dof_date
from company.signals.signals_for_FireRun import _sync_employee_last_firerun_date


# python manage.py updateLastFireFromFireRunCommand
class Command(BaseCommand):
    help = "Run updateLastFireFromFireRunCommand"

    def handle(self, *args, **options):
        qs = Employees.objects.all().order_by("id").iterator()
        for emp in qs:
            print("id:", emp.id)
            _sync_employee_last_firerun_date(emp.id)
            _sync_employee_last_dof_date(emp.id)
        self.stdout.write(self.style.SUCCESS("updateLastFireFromFireRunCommand done.\n"))