import json

from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest

from company.models import Employees
from company.services.EmployeesService import EmployeesService
from core.tasks import handle_sync_delivery_log_task
from exchange.models import Contacts_Prop
from synchronization.models import Sync_Delivery_Logs
from synchronization.services.SyncDeliveryService import SyncDeliveryService


def update_employee_parameters(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST allowed")

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = "django"

    employee_id = data.pop("employee_id")
    csrfmiddlewaretoken = data.pop("csrfmiddlewaretoken", None)

    employee = Employees.objects.get(id=employee_id)
    # employee.last_modified_time = datetime.now().astimezone()
    employee.last_modified_name = username
    employee.save()

    employees_service = EmployeesService()
    employees_service.set_contact(employee_obj=employee)

    for param_id, param_value in data.items():
        contacts_prop_obj = Contacts_Prop.objects.get(id=param_id)
        employees_service.set_contact_parameters(contacts_prop_obj, param_value)

    employees_service.do_update_or_create_contact_parameters(modified_by=username)
    changed_parameters = employees_service.get_all_changed_parameters_obj()
    old_parameters = employees_service.get_old_parameters_obj()

    sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
        employee=employee,
        changed_parameters=changed_parameters,
        old_parameters=old_parameters,
        target_system=Sync_Delivery_Logs.TargetSystemChoices.PRIVSER,
        modified_by=username
    )
    for sync_delivery_log_id in sync_delivery_log_ids:
        if settings.DEBUG:
            handle_sync_delivery_log_task.run(sync_delivery_log_id)
        else:
            handle_sync_delivery_log_task.delay(sync_delivery_log_id) #good

    sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
        employee=employee,
        changed_parameters=changed_parameters,
        old_parameters=old_parameters,
        target_system=Sync_Delivery_Logs.TargetSystemChoices.EXCHANGE,
        modified_by=username
    )
    for sync_delivery_log_id in sync_delivery_log_ids:
        if settings.DEBUG:
            handle_sync_delivery_log_task.run(sync_delivery_log_id)
        else:
            handle_sync_delivery_log_task.delay(sync_delivery_log_id) #good

    return JsonResponse({"status": "ok"})
