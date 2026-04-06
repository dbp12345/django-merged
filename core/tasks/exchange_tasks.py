from celery import shared_task

from core.task_toggle import is_task_enabled


@shared_task(
    name="update_from_exchange",
    autoretry_for=(Exception,),  # Автоматически ретраить при любых исключениях
    retry_kwargs={'max_retries': 25, 'countdown': 60},  # До 25 повторов, с задержкой 60 сек
    retry_backoff=False,  # Экспоненциальное увеличение задержки между ретраями
    retry_jitter=True  # Добавляет случайную задержку для предотвращения одновременных повторов
)
def update_from_exchange_task(**kwargs):
    if not is_task_enabled("update_from_exchange_task"):
        return None

    from exchange.services.ExchangeUpdatesService import ExchangeUpdatesService
    return ExchangeUpdatesService.do_update_from_exchange_sub(
        offset=kwargs.get('offset'),
        batch_size=kwargs.get('batch_size'),
        datetime_after=kwargs.get('datetime_after'),
        datetime_after_str=kwargs.get('datetime_after_str'),
        datetime_before_str=kwargs.get('datetime_before_str'),
        ignore_diff_properties=kwargs.get('ignore_diff_properties', False)
    )

@shared_task(
    name="update_unprocessed_from_exchange",
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 5, 'countdown': 60},
    retry_backoff=False,
    retry_jitter=True
)
def update_unprocessed_from_exchange_task(**kwargs):
    if not is_task_enabled("update_unprocessed_from_exchange_task"):
        return None

    from exchange.services.ExchangeUpdatesService import ExchangeUpdatesService
    return ExchangeUpdatesService.do_update_unprocessed_from_exchange(
        ignore_diff_properties=kwargs.get('ignore_diff_properties', False)
    )
