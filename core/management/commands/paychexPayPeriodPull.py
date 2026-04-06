from django.core.management.base import BaseCommand
from paychex.services import PaychexPayPeriodService


class Command(BaseCommand):
    help = "Run paychexPayPeriodPull"

    def add_arguments(self, parser):
        parser.add_argument(
            "--param",
            type=str,
            help="Param",
        )

    def handle(self, *args, **options):
        paychexPayPeriodService = PaychexPayPeriodService
        paychexPayPeriodService.sync_payperiod_from_api(
            from_date="2000-01-01T00:00:00Z", to_date="2050-01-01T00:00:00Z"
        )

        self.stdout.write(self.style.SUCCESS("Finished."))
