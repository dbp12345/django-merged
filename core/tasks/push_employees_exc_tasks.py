import traceback
from celery import shared_task
from exchangelib.errors import MultipleObjectsReturned, DoesNotExist

from core.exceptions import StopTask
from core.task_toggle import is_task_enabled
from exchange.services.ExchangeApiService import ExchangeApiService


@shared_task(
    name="push_update_exc_contact",
    queue="exchange_throttled",
    autoretry_for=(Exception,),  # Автоматически ретраить при любых исключениях
    retry_kwargs={'max_retries': 240, 'countdown': 60},  # До 100 повторов, с задержкой 60 сек
    retry_backoff=False,  # Экспоненциальное увеличение задержки между ретраями
    retry_jitter=True  # Добавляет случайную задержку для предотвращения одновременных повторов
)
def update_exc_contact_by_email_with_data_task(email, data, log_id=None):
    if not is_task_enabled("update_exc_contact_by_email_with_data_task"):
        return None

    from synchronization.models import Sync_Delivery_Logs

    try:
        ExchangeApiService.update_exc_contact_by_email_with_data(email=email, data=data)
        if log_id:
            Sync_Delivery_Logs.objects.filter(id=log_id).update(
                status_code=Sync_Delivery_Logs.StatusCode.SYNC_COMPLETED.value,
                body={}
            )
    except MultipleObjectsReturned as e:
        if log_id:
            Sync_Delivery_Logs.objects.filter(id=log_id).update(
                status_code=Sync_Delivery_Logs.StatusCode.MULTIPLE_CONTACT_LINK.value,
                body={"message": str(e)}
            )
        return
    except DoesNotExist as e:
        if log_id:
            Sync_Delivery_Logs.objects.filter(id=log_id).update(
                status_code=Sync_Delivery_Logs.StatusCode.NO_CONTACT_LINK.value,
                body={"message": str(e)}
            )
        return
    except StopTask as e:
        if log_id:
            Sync_Delivery_Logs.objects.filter(id=log_id).update(
                status_code=e.status_code,
                body={"message": e.message}
            )
        return
    except Exception:
        if log_id:
            Sync_Delivery_Logs.objects.filter(id=log_id).update(
                status_code=Sync_Delivery_Logs.StatusCode.PROCESSING_ERROR.value,
                body={"error": traceback.format_exc()}
            )
        raise
