from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from core.tasks import handle_sync_delivery_log_task
from synchronization.models import Sync_Parameters_Logs, Sync_Delivery_Logs
from synchronization.services.SyncInstantService import SyncInstantService


class Command(BaseCommand):
    help = "repeatSyncParametersLogsCommand"

    def handle(self, *args, **options):
        print("-=start=-")

        # system = "old_sync"
        system = "new_delivery"

        # if system == "old_sync":
        #     ids = list(Sync_Parameters_Logs.objects.filter(
        #         status_code__in=(Sync_Parameters_Logs.StatusCode.ERROR_API, Sync_Parameters_Logs.StatusCode.IN_PROGRESS)
        #     ).values_list("id", flat=True))
        #
        #     for sync_parameters_logs_id in ids:
        #         print("sync_parameters_logs_id: ", sync_parameters_logs_id)
        #         SyncInstantService.repeat_update_remote_contacts(sync_parameters_logs_id=sync_parameters_logs_id)

        if system == "new_delivery":
            ids = list(Sync_Delivery_Logs.objects.filter(
                status_code__in=(
                    Sync_Delivery_Logs.StatusCode.NEW.value,
                    Sync_Delivery_Logs.StatusCode.NOT_PROCESSED.value,
                    Sync_Delivery_Logs.StatusCode.PROCESSING_ERROR.value,
                    # Sync_Delivery_Logs.StatusCode.EXTERNAL_API_ERROR.value,
                )
            ).values_list("id", flat=True))

            for sync_delivery_log_id in ids:
                if settings.DEBUG:
                    handle_sync_delivery_log_task.run(sync_delivery_log_id)
                else:
                    transaction.on_commit(lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(sync_id))
                    # handle_sync_delivery_log_task.delay(sync_delivery_log_id)
                print("sync_parameters_logs_id: ", sync_delivery_log_id)

        print("-=end=-")
