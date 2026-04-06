from celery import shared_task

from core.exceptions import StopTask
from core.task_toggle import is_task_enabled


@shared_task(
    name="update_from_privser",
    autoretry_for=(Exception,),  # Автоматически ретраить при любых исключениях
    retry_kwargs={'max_retries': 15, 'countdown': 60},  # До 5 повторов, с задержкой 60 сек
    retry_backoff=False,  # Экспоненциальное увеличение задержки между ретраями
    retry_jitter=True,  # Добавляет случайную задержку для предотвращения одновременных повторов
    rate_limit="10/s"
)
def update_from_privser_task(**kwargs):
    if not is_task_enabled("update_from_privser_task"):
        return None

    from privser.services.PrivserUpdatesService import PrivserUpdatesService
    try:
        return PrivserUpdatesService.update_all_fields_from_contact_id(
            contact_id=kwargs.get("contact_id"),
            ignore_diff_properties=kwargs.get("ignore_diff_properties", False)
        )
    except StopTask as e:
        return None