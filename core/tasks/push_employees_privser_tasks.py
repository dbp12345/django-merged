import traceback
from celery import shared_task

from core.exceptions import StopTask
from core.task_toggle import is_task_enabled
from privser.services.PrivserAPI2Service import PrivserAPI2Service


@shared_task(
    name="push_update_privser_contact",
    autoretry_for=(Exception,),  # Автоматически ретраить при любых исключениях
    retry_kwargs={'max_retries': 15, 'countdown': 60},  # До 5 повторов, с задержкой 60 сек
    retry_backoff=False,  # Экспоненциальное увеличение задержки между ретраями
    retry_jitter=True  # Добавляет случайную задержку для предотвращения одновременных повторов
)
def update_privser_contact_task(contact_id, main_fields, custom_fields_list, log_id=None):
    if not is_task_enabled("update_privser_contact_task"):
        return None

    from synchronization.models import Sync_Delivery_Logs

    try:
        privser_api2_service = PrivserAPI2Service()
        response_privser = privser_api2_service.update_contacts_fields(
            contact_id=contact_id,
            main_fields=main_fields,
            custom_fields_list=custom_fields_list
        )

        privser_api2_service.check_uploaded_custom_field_with(custom_fields_list, response_privser, raise_on_mismatch=True)

        if log_id:
            is_succeded = response_privser.get("succeded")
            if is_succeded is True:
                Sync_Delivery_Logs.objects.filter(id=log_id).update(
                    status_code="Sync Completed",
                    body={}
                )
            else:
                Sync_Delivery_Logs.objects.filter(id=log_id).update(
                    status_code="External API Error",
                    body=response_privser
                )
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
                status_code="Processing Error",
                body={"error": traceback.format_exc()}
            )
        raise
