from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from company.models import Employees
from company.services.EmployeesService import EmployeesService
from core.tasks import handle_sync_delivery_log_task
from exchange.models import Contacts_Prop
from synchronization.models import Sync_Delivery_Logs
from synchronization.services.SyncDeliveryService import SyncDeliveryService


# python manage.py testChangeParamCommand
class Command(BaseCommand):
    help = "Run testChangeParamCommand"

    def add_arguments(self, parser):
        parser.add_argument(
            "--param",
            type=str,
            help="Param",
        )

    def handle(self, *args, **options):

        param = options.get("param")

        email = "Test12@Automation.com"

        employee = Employees.objects.get(email=email)

        employees_service = EmployeesService()
        employees_service.set_contact(employee_obj=employee)

        data = {
            "123": "JT-new-127",
            "140": "FN-new-127",
        }

        for param_id, param_value in data.items():
            contacts_prop_obj = Contacts_Prop.objects.get(id=param_id)
            employees_service.set_contact_parameters(contacts_prop_obj, param_value)

        employees_service.do_update_or_create_contact_parameters(modified_by="Test_new")
        changed_parameters = employees_service.get_all_changed_parameters_obj()
        old_parameters = employees_service.get_old_parameters_obj()



        print("changed_parameters", changed_parameters)
        print("old_parameters", old_parameters)

        sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
            employee=employee,
            changed_parameters=changed_parameters,
            old_parameters=old_parameters,
            target_system=Sync_Delivery_Logs.TargetSystemChoices.PRIVSER,
            modified_by="Test_new"
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
            modified_by="Test_new"
        )
        for sync_delivery_log_id in sync_delivery_log_ids:
            if settings.DEBUG:
                handle_sync_delivery_log_task.run(sync_delivery_log_id)
            else:
                transaction.on_commit(lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(sync_id))
                # handle_sync_delivery_log_task.delay(sync_delivery_log_id)
