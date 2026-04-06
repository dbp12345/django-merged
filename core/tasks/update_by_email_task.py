from celery import shared_task


@shared_task(
    name="update_by_email_task",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 500, "countdown": 60},  # Меньше задержка, быстрее будет
    retry_backoff=False,
    retry_jitter=True
)
def update_by_email_task(email, ignore_diff_properties = True):
    from exchange.services.ExchangeUpdatesService import ExchangeUpdatesService
    ExchangeUpdatesService.do_update_from_exchange_by_email(email=email, ignore_diff_properties=ignore_diff_properties)