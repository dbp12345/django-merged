from django.core.management.base import BaseCommand
from paychex.services import PaychexAllService


class Command(BaseCommand):
    help = "Run paychexAllPull"

    def add_arguments(self, parser):
        parser.add_argument(
            "--param",
            type=str,
            help="Param",
        )

    def handle(self, *args, **options):
        paychexAllService = PaychexAllService
        paychexAllService.update_only_current_all()
        self.stdout.write(self.style.SUCCESS("Finished."))
