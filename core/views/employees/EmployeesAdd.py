from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View

from company.models import Employees
from company.services.EmployeesService import EmployeesService
from core.tasks import handle_sync_delivery_log_task
from exchange.models import Contacts_Prop
from privser.services.PrivserAPI2Service import PrivserAPI2Service
from privser.services.PrivserUpdatesService import PrivserUpdatesService
from synchronization.models import Sync_Delivery_Logs
from synchronization.services.SyncDeliveryService import SyncDeliveryService


@method_decorator(staff_member_required, name="dispatch")
class EmployeesAdd(View):
    def get(self, request, *args, **kwargs):
        title = "Add employee"

        context = {
            "title": title,
        }
        return render(request, "admin/employees/add_employee.html", context)

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            username = request.user.username
        else:
            username = "django"

        param_name = "Email"
        param_value = request.POST.get("email")
        # param_value = request.POST.get("param_value")

        contacts_prop_obj = Contacts_Prop.objects.get(property_name=param_name)

        employees_service = EmployeesService()
        employee, created = employees_service.update_or_create_contact(
            contact_id=param_value,
            email=param_value,
            last_modified_name=username,
            last_modified_time=datetime.now().astimezone(),
            datetime_created=datetime.now().astimezone(),
        )

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
                # handle_sync_delivery_log_task.delay(sync_delivery_log_id)


        try:
            cont = PrivserAPI2Service().get_contacts_by_email(email=param_value)["contact"][0]
            contact_id = cont.get("id")
            PrivserUpdatesService.update_all_fields_from_contact_id(contact_id=contact_id, ignore_diff_properties=False)
        except Exception:
            pass

        return redirect("admin:%s_%s_change" % (Employees._meta.app_label, Employees._meta.model_name), employee.id)
        return JsonResponse({"status": "success"})
