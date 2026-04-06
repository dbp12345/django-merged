from django.core.management.base import BaseCommand
from privser.services.PrivserUpdatesService import PrivserUpdatesService


# python manage.py updateLastModifiedContactsPrivserCommand
class Command(BaseCommand):
    help = "Run updateLastModifiedContactsPrivserCommand"

    def add_arguments(self, parser):
        parser.add_argument(
            "--ignore_diff_properties",
            action="store_true",
            help="ignore_diff_properties",
        )

    def handle(self, *args, **options):
        ignore_diff_properties = options["ignore_diff_properties"]
        list_of_changed_emails = PrivserUpdatesService.do_update_from_privser_by_last_modified_time(task=True, ignore_diff_properties=ignore_diff_properties)
        if list_of_changed_emails:
            self.stdout.write(self.style.SUCCESS("updateLastModifiedContactsPrivser done.") + "\n")
            self.stdout.write(self.style.SUCCESS(str(list_of_changed_emails)) + "\n")
