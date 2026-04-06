from celery import shared_task

from company.services.EmployeesService import EmployeesService
from core.task_toggle import is_task_enabled


@shared_task(
    name="generate_entities_from_contact_params",
    autoretry_for=(Exception,),  # Автоматически ретраить при любых исключениях
    retry_kwargs={'max_retries': 5, 'countdown': 60},  # До 5 повторов, с задержкой 60 сек
    retry_backoff=False,  # Экспоненциальное увеличение задержки между ретраями
    retry_jitter=True  # Добавляет случайную задержку для предотвращения одновременных повторов
)
def generate_entities_from_contact_params_task(employee_id):
    if not is_task_enabled("generate_entities_from_contact_params_task"):
        return

    EmployeesService.generate_entities_from_contact_params(employee_id=employee_id)
