from celery import shared_task

from company.models import Employees, Employees_Parameters


@shared_task(
    name="check_possibility_firecrew_task",
    autoretry_for=(Exception,),  # Автоматически ретраить при любых исключениях
    retry_kwargs={'max_retries': 3, 'countdown': 20},  # До 5 повторов, с задержкой 60 сек
    retry_backoff=False,  # Экспоненциальное увеличение задержки между ретраями
    retry_jitter=True  # Добавляет случайную задержку для предотвращения одновременных повторов
)
def check_possibility_firecrew_task(employee_id):
    employee = Employees.objects.get(pk=employee_id)
    if employee.fire_crew:
        if not employee.is_manifested:
            employee.fire_crew = None
            employee.save(update_fields=["fire_crew"])
        else:
            not_eligible_to_work = Employees_Parameters.objects.filter(
                employee=employee,
                contacts_prop__property_name="Not Eligible to Work (Button)"
            ).first()

            if not_eligible_to_work and not_eligible_to_work.value_bool:
                employee.fire_crew = None
                employee.save(update_fields=["fire_crew"])
