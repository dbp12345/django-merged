from django.conf import settings
from django.db import transaction

from company.models import Employees, FireRun
from company.services.EmployeesService import EmployeesService
from exchange.models import Contacts_Prop
from synchronization.models import Sync_Delivery_Logs
from synchronization.services.SyncDeliveryService import SyncDeliveryService
from core.tasks import handle_sync_delivery_log_task


class LastFireService:

    @staticmethod
    def set_employee_latest_fire_run_date(employee_id: int = None, employee: Employees = None):
        # CHANGED: allow optional single-employee recalculation
        if employee_id is not None and employee is None:
            employee = Employees.objects.get(id=employee_id)


        latest_fire_run_date = LastFireService.get_employee_latest_fire_run_date(
            employee=employee
        )

        employees_service = EmployeesService()
        employees_service.set_contact(employee_obj=employee)

        contacts_prop_obj = Contacts_Prop.objects.get(property_name="Last Fire")
        employees_service.set_contact_parameters(contacts_prop_obj, latest_fire_run_date)

        employees_service.do_update_or_create_contact_parameters(modified_by=None)
        changed_parameters = employees_service.get_all_changed_parameters_obj()
        old_parameters = employees_service.get_old_parameters_obj()

        sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
            employee=employee,
            changed_parameters=changed_parameters,
            old_parameters=old_parameters,
            target_system=Sync_Delivery_Logs.TargetSystemChoices.PRIVSER,
            modified_by=None
        )
        for sync_delivery_log_id in sync_delivery_log_ids:
            if settings.DEBUG:
                handle_sync_delivery_log_task.run(sync_delivery_log_id)
            else:
                transaction.on_commit(lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(sync_id))

        sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
            employee=employee,
            changed_parameters=changed_parameters,
            old_parameters=old_parameters,
            target_system=Sync_Delivery_Logs.TargetSystemChoices.EXCHANGE,
            modified_by=None
        )
        for sync_delivery_log_id in sync_delivery_log_ids:
            if settings.DEBUG:
                handle_sync_delivery_log_task.run(sync_delivery_log_id)
            else:
                transaction.on_commit(lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(sync_id))


    # @staticmethod
    # def get_employees_latest_fire_run_dates(employee_ids: Optional[Iterable[int]] = None) -> Dict[int, Optional[models.DateField]]:
    #     """
    #     Return mapping employee_id -> latest FireRun.start_date (or None).
    #     # Comment: efficient aggregate using Max on related_name "fire_run_entries".
    #     """
    #     qs = Employees.objects.all()
    #     if employee_ids is not None:
    #         qs = qs.filter(id__in=employee_ids)
    #
    #     qs = qs.annotate(latest_start=Max("fire_run_entries__start_date")).values("id", "latest_start")
    #
    #     # build dict
    #     return {item["id"]: item["latest_start"] for item in qs}

    @staticmethod
    def get_employee_latest_fire_run_date(employee: Employees):
        """
        Return the latest FireRun.start_date for a single employee or None.
        # Comment: simple direct query ordering by start_date for best precision.
        """
        return (
            FireRun.objects
            .filter(employee=employee, start_date__isnull=False)
            .order_by("-start_date")
            .values_list("start_date", flat=True)
            .first()
        )
