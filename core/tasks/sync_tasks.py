import traceback

from celery import shared_task

from core.exceptions import StopTask
from core.task_toggle import is_task_enabled
from synchronization.models import Sync_Delivery_Logs
from synchronization.services.SyncDeliveryService import SyncDeliveryService


@shared_task(
    name="handle_sync_delivery_log",
    autoretry_for=(Exception,),  # Автоматически ретраить при любых исключениях
    retry_kwargs={'max_retries': 50, 'countdown': 60},  # До N повторов, с задержкой N сек
    retry_backoff=False,  # Экспоненциальное увеличение задержки между ретраями
    retry_jitter=True  # Добавляет случайную задержку для предотвращения одновременных повторов
)
def handle_sync_delivery_log_task(sync_delivery_logs_id):
    if not is_task_enabled("handle_sync_delivery_log_task"):
        return None

    try:
        SyncDeliveryService.handle_sync_delivery_log(sync_delivery_logs_id)
    except StopTask as e:
        Sync_Delivery_Logs.objects.filter(id=sync_delivery_logs_id).update(
            status_code=e.status_code,
            body={"message": e.message}
        )
        return
    except Exception:
        Sync_Delivery_Logs.objects.filter(id=sync_delivery_logs_id).update(
            status_code=Sync_Delivery_Logs.StatusCode.PROCESSING_ERROR.value,
            body={"error": traceback.format_exc()}
        )
        raise
