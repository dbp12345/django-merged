from django.core.management.base import BaseCommand
from exchange.services.ExchangeUpdatesService import ExchangeUpdatesService
from core.tasks.exchange_tasks import update_unprocessed_from_exchange_task


# python manage.py runUpdateFromExchangeCommand --ignore_diff_properties этого достаточно, чтобы обновить все контакты без изменённых параметров
# python manage.py runUpdateFromExchangeCommand --ignore_diff_properties --update_all --after_date="2024-12-23 14:30:00"
class Command(BaseCommand):
    help = "Run UpdateFromExchange"

    def add_arguments(self, parser):
        parser.add_argument(
            "--ignore_diff_properties",
            action="store_true",
            help="ignore_diff_properties",
        )

        parser.add_argument(
            "--update_all",
            action="store_true",
            help="update_all",
        )

        parser.add_argument(
            "--after_date",
            type=str,
            help="Specify the start date and time in the format YYYY-MM-DD HH:MM:SS",
        )

        parser.add_argument(
            "--page_number",
            type=int,
        )

    def handle(self, *args, **options):
        ignore_diff_properties = options["ignore_diff_properties"]
        after_date_str = options.get("after_date")
        update_all = options.get("update_all")
        page_number = options.get("page_number")


        if after_date_str:
            ExchangeUpdatesService.do_update_from_exchange_handle(ignore_diff_properties=ignore_diff_properties, after_date_str=after_date_str)
        elif page_number is not None:
            batch_size = 100
            ExchangeUpdatesService.do_update_from_exchange_sub(
                offset=page_number * batch_size,
                batch_size=batch_size,
                ignore_diff_properties=ignore_diff_properties
            )
        elif update_all:
            ExchangeUpdatesService.do_update_from_exchange_handle(ignore_diff_properties=ignore_diff_properties, update_all=update_all)
        else:
            # ExchangeUpdatesService.do_update_unprocessed_from_exchange(ignore_diff_properties=ignore_diff_properties)
            update_unprocessed_from_exchange_task.apply_async(ignore_diff_properties=ignore_diff_properties)
        # self.stdout.write(self.style.SUCCESS("UpdateFromExchange done.") + "\n")

    # def handle_OLD(self, *args, **options):
    #     lock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runUpdateFromExchangeCommand.lock")
    #     formatted_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #
    #     if os.path.exists(lock_file):
    #         # If Lock file is older than N seconds. Deleting it...
    #         file_age_seconds = time.time() - os.path.getmtime(lock_file)
    #         self.stdout.write(self.style.NOTICE(f"The existence of the lock file is {file_age_seconds} second`s"))
    #         Cron_Logs.objects.create(body={f"The existence of the lock file is {file_age_seconds} second`s"})
    #         if file_age_seconds > 3600:
    #             self.stdout.write(self.style.WARNING("Lock file is older than 1 hour."))
    #             self.stdout.write(self.style.NOTICE("Removing lock file."))
    #             os.remove(lock_file)
    #             return
    #         if ignore_lock is False:
    #             self.stdout.write(self.style.WARNING("The command is already running."))
    #             return
    #     else:
    #         with open(lock_file, "w") as f:
    #             self.stdout.write(self.style.NOTICE("Creating lock file.."))
    #             f.write(str(os.getpid()) + "\n")
    #
    #     try:
    #         self.stdout.write(self.style.NOTICE(str(formatted_datetime)))
    #         list_of_changed_emails = []
    #         emails = {}
    #         if list_of_changed_emails:
    #             emails = {"emails": str(list_of_changed_emails)}
    #
    #         Cron_Logs.objects.create(body={"date": str(formatted_datetime), **emails})
    #     except Exception as e:
    #         self.stdout.write(self.style.ERROR(str(e)))
    #         self.stdout.write(self.style.ERROR(traceback.format_exc()))
    #         Cron_Logs.objects.create(body={str(e)})
    #         # return {"status": Contacts_Prop_Logs.StatusCode.CRITICAL, "error": f"{e} + {traceback.format_exc()}"}
    #
    #     self.stdout.write(self.style.NOTICE("Removing lock file."))
    #     os.remove(lock_file)
    #     self.stdout.write(self.style.SUCCESS("Done") + "\n")
