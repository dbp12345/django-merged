from django.core.management.base import BaseCommand

from paychex.models import PayPeriod
from paychex.services import PaychexPaycheckService


class Command(BaseCommand):
    help = "Run paychexPaycheckPull"

    def add_arguments(self, parser):
        parser.add_argument(
            "--param",
            type=str,
            help="Param",
        )

    def handle(self, *args, **options):
        # TODO делать синхронизацию от последней даты, чтобы не всех тянуть....
        paychexPaycheckService = PaychexPaycheckService

        pay_period_instance = PayPeriod.objects.filter()
        for pay_period in pay_period_instance:
            paychexPaycheckService.sync_checks_for_payperiod(payperiod_id=pay_period.payperiod_id)

        # paychexPaycheckService.sync_checks_for_payperiod(payperiod_id="1020053160696039")

        self.stdout.write(self.style.SUCCESS("Finished."))
