from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseRedirect
from django.db import transaction

from company.models import DispatchStatus
from company.services.EmployeesService import EmployeesService
from core.tasks import handle_sync_delivery_log_task
from dispatch.models import Dispatch
from dispatch.models.Dispatch import Status
from exchange.models import Contacts_Prop
from synchronization.models import Sync_Delivery_Logs
from synchronization.services.SyncDeliveryService import SyncDeliveryService


@staff_member_required
def dispatch_set_global_status(request, status, obj_id):
    if not request.user.is_authenticated:
        return JsonResponse({"errors": "You are not authorized to view this page."}, status=403)

    status_map = {
        "Not On Fire": (Status.NOT_ON_FIRE, DispatchStatus.NOT_ON_FIRE.value[0]),
        "On Fire": (Status.ON_FIRE, DispatchStatus.ON_FIRE.value[0]),
    }
    if status not in status_map:
        return JsonResponse({"errors": f"Unknown status: {status}"}, status=400)

    dispatch_status, employee_status = status_map[status]

    dispatch = (
        Dispatch.objects
        .prefetch_related(
            "equipment_group",
            "equipment_group__nomex_entries",
            "equipment_group__saws_entries",
            "equipment_group__truck_entries",
            "equipment_group__radio_entries",
            "equipment_group__phone_entries",
            "crew__employees",
        )
        .get(pk=obj_id)
    )

    username = request.user.username if request.user.is_authenticated else "django"

    with transaction.atomic():
        # Update dispatch status
        dispatch.status = dispatch_status
        dispatch.save()

        groups = list(dispatch.equipment_group.all())
        for eg in groups:
            eg.status = dispatch_status
            eg.save(update_fields=["status", "updated_at"])

            # CHANGED: bulk update children by type (faster and simpler than per-item loops)
            eg.nomex_entries.update(status=dispatch_status)
            eg.saws_entries.update(status=dispatch_status)
            eg.truck_entries.update(status=dispatch_status)
            eg.radio_entries.update(status=dispatch_status)
            eg.phone_entries.update(status=dispatch_status)

        # Update crew employees + sync
        if dispatch.crew and employee_status:
            employees = dispatch.crew.employees.all()
            if employees:
                param_name = "Dispatch Call Status"
                contacts_prop_obj = Contacts_Prop.objects.get(property_name=param_name)

                for employee in employees:
                    employee.last_modified_name = username
                    employee.save(update_fields=["last_modified_name", "updated_at"])

                    employees_service = EmployeesService()
                    employees_service.set_contact(employee_obj=employee)
                    employees_service.set_contact_parameters(contacts_prop_obj, employee_status)
                    employees_service.do_update_or_create_contact_parameters(modified_by=username)

                    changed_parameters = employees_service.get_all_changed_parameters_obj()
                    old_parameters = employees_service.get_old_parameters_obj()

                    # print("changed_parameters:", changed_parameters)
                    # print("old_parameters:", old_parameters)

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
                            transaction.on_commit(lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(sync_id))
                            # handle_sync_delivery_log_task.delay(sync_delivery_log_id)

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
                            transaction.on_commit(lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(sync_id))

    referer = request.META.get("HTTP_REFERER", "/admin/")
    return HttpResponseRedirect(referer)
