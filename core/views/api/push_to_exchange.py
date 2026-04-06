from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect

from company.models import Employees
from core.tasks import handle_sync_delivery_log_task
from privser.models import Contacts as ContactsPrivser
from synchronization.models import Sync_Delivery_Logs
from synchronization.services.SyncDeliveryService import SyncDeliveryService


@staff_member_required
def forcepush_to_exchange(request, obj_id):
    if not request.user.is_authenticated:
        return JsonResponse({"errors": "You are not authorized to view this page."}, status=403)

    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = "forcepush"

    employee = Employees.objects.get(id=obj_id)

    changed_parameters = {}
    old_parameters = {}
    for employees_parameters_i in employee.employees_parameters_entries.only("contacts_prop", "value"):
        changed_parameters[employees_parameters_i.contacts_prop] = employees_parameters_i.value
        old_parameters[employees_parameters_i.contacts_prop] = employees_parameters_i.value

    sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
        employee=employee,
        changed_parameters=changed_parameters,
        old_parameters=old_parameters,
        target_system=Sync_Delivery_Logs.TargetSystemChoices.EXCHANGE,
        modified_by=username
    )
    for sync_delivery_log_id in sync_delivery_log_ids:
        # try:
        #     print("no_queue = True: True")
        #     handle_sync_delivery_log_task.run(sync_delivery_log_id, no_queue = True)
        # except Exception as e:
        #     return JsonResponse({"errors": str(e)})
        # handle_sync_delivery_log_task.run(sync_delivery_log_id, no_queue = True)
        if settings.DEBUG:
            handle_sync_delivery_log_task.run(sync_delivery_log_id)
        else:
            from django.db import transaction
            transaction.on_commit(lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(sync_id))
            # handle_sync_delivery_log_task.delay(sync_delivery_log_id)

    referer = request.META.get('HTTP_REFERER')
    return HttpResponseRedirect(referer)

@staff_member_required
def remove_from_system(request, obj_id):
    try:
        email = Employees.objects.get(id=obj_id).email
        ContactsPrivser.objects.get(email=email).delete()
    except Exception as e:
        pass

    from django.db import connection

    table = Employees._meta.db_table

    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM {table} WHERE id = %s", [obj_id])

    return redirect("employees_table")
