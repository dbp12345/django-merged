from django.core.management.base import BaseCommand
from paychex.services import PaychexCompanyWorkersService


class Command(BaseCommand):
    help = "Run paychexCompanyWorkersPull"

    def add_arguments(self, parser):
        parser.add_argument(
            "--param",
            type=str,
            help="Param",
        )

    def handle(self, *args, **options):
        paychexCompanyWorkersService = PaychexCompanyWorkersService
        paychexCompanyWorkersService.sync_company_workers_from_api()

        self.stdout.write(self.style.SUCCESS("Finished."))
