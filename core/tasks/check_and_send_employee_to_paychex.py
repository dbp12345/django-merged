from celery import shared_task
from django.utils.timezone import now
from company.models import Employees, Employees_Parameters
from core.task_toggle import is_task_enabled
from exchange.models import Contacts_Prop
from paychex.services.PaychexService import PaychexService


@shared_task(
    name="check_and_send_employee_to_paychex",
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 15, 'countdown': 90},
    retry_backoff=False,
    retry_jitter=True
)
def check_and_send_employee_to_paychex(employee_id: int):
    if not is_task_enabled("check_and_send_employee_to_paychex"):
        return

    try:
        employee = Employees.objects.get(id=employee_id)
    except Employees.DoesNotExist:
        return

    rating_prop = Contacts_Prop.objects.get(property_name="Rating")
    training_prop = Contacts_Prop.objects.get(property_name="Field Training")

    rating_param = Employees_Parameters.objects.filter(
        employee=employee, contacts_prop=rating_prop
    ).first()

    training_param = Employees_Parameters.objects.filter(
        employee=employee, contacts_prop=training_prop
    ).first()

    if not rating_param or rating_param.value != "E":
        return

    if not training_param or not training_param.value:
        return

    training_date = training_param.value_date.date()

    if (now().date() - training_date).days > 7:
        return

    PaychexService.create_progress_worker_in_paychex(employee)
