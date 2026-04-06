from django.core.management.base import BaseCommand
from paychex.services.punch_upsert import upsert_timepunch_rows_and_sync, get_admins_companyworker_employee_ids


# python manage.py getPunchesFromPaychexCommand

class Command(BaseCommand):
    help = "Run getPunchesFromPaychexCommand"

    def add_arguments(self, parser):
        parser.add_argument(
            "--param",
            type=str,
            help="Param",
        )

    def handle(self, *args, **options):
        ids = get_admins_companyworker_employee_ids()  # [2171, 2175]

        try:

            res = upsert_timepunch_rows_and_sync(ids, sync=True)
            # print(res)

            # per_emp = svc.get_status_per_employee(rows=rows, tz=tz)

            # is_online = svc._is_online_today(rows, tz)
            # last_in, last_out = svc._find_last_punches_for_today(rows, tz)
            self.stderr.write(self.style.NOTICE(str(res)))

        except Exception as e:
            self.stderr.write(self.style.WARNING(str(e)))
