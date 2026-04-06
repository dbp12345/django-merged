import json
from datetime import datetime
from django.core.management.base import BaseCommand

from privser.services.PrivserUpdatesService import PrivserUpdatesService


# python manage.py runUpdateFromPrivserCommand --ignore_diff_properties [1733418393723, 'NCebHd54oUoRTyTqcvYm']
# python manage.py runUpdateFromPrivserCommand --ignore_diff_properties --query="startAfter=1679444050142&startAfterId=QArr9VUbIQ6CQHHMQqr5" тест последних пару страниц

# python manage.py runUpdateFromPrivserCommand --ignore_diff_properties --query='{"searchAfter": [1679444050142, "QArr9VUbIQ6CQHHMQqr5"]}' - так сработало на проде через Git Bash

# python manage.py runUpdateFromPrivserCommand --ignore_diff_properties - если падает, то смотрим в консоли query и стартуем с него
# --query='{\"filters\": [{\"field\": \"dateUpdated\", \"operator\": \"range\", \"value\": {\"gt\": \"2025-01-25T00:00:00.000Z\"}}]}'
# --query "{\"filters\": [{\"field\": \"dateUpdated\", \"operator\": \"range\", \"value\": {\"gt\": \"2025-01-10T00:00:00.000Z\"}}]}"
# 'total': 45219,
class Command(BaseCommand):
    help = "Run UpdateFromPrivserCommand"

    def add_arguments(self, parser):
        parser.add_argument(
            "--ignore_diff_properties",
            action="store_true",
            help="ignore_diff_properties",
        )

        parser.add_argument(
            "--param1",
            type=str,
            help="param1",
        )

        parser.add_argument(
            "--param2",
            type=str,
            help="param2",
        )

        parser.add_argument(
            "--query",
            type=str,
            help="query",
        )

    def handle(self, *args, **options):
        ignore_diff_properties = options["ignore_diff_properties"]
        param1 = options.get("param1")
        param2 = options.get("param2")
        query_str = options.get("query")

        if query_str:
            query_str = json.loads(options.get("query"))

        formatted_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.stdout.write(self.style.NOTICE(str(formatted_datetime)))

        PrivserUpdatesService.get_and_update_all_fields_for_all_contacts(param1=param1, param2=param2, query=query_str, ignore_diff_properties=ignore_diff_properties)

        formatted_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.stdout.write(self.style.NOTICE(str(formatted_datetime)))
        # self.stdout.write(self.style.NOTICE(str(list_of_changed_emails)))

        self.stdout.write(self.style.SUCCESS("UpdateFromPrivser done.") + "\n")
