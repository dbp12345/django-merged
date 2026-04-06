from django.db.models import Max
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import transaction

from company.models import Employees, FireRun
from exchange.models import Contacts_Prop

from synchronization.services.SyncDeliveryService import SyncDeliveryService
from core.services.RecordsService import RecordsService


def _sync_employee_last_firerun_date(employee_id: int) -> None:
    if not employee_id:
        return

    # changed: single aggregate query (fewer queries, no ORDER BY)
    # max_date =  (
    #     FireRun.objects
    #     .filter(employee_id=employee_id, start_date__isnull=False)
    #     .order_by("-start_date")
    #     .values_list("start_date", flat=True)
    #     .first()
    # )
    max_date = FireRun.objects.filter(
        employee_id=employee_id, start_date__isnull=False
    ).aggregate(m=Max("start_date"))["m"]

    # changed: no date -> nothing to sync (keeps current value intact)
    if not max_date:
        return

    # changed: safe fetch; do not crash the signal if employee is gone
    employee_instance = Employees.objects.filter(id=employee_id).first()
    if not employee_instance:
        return

    property_name = "Last Fire"
    contacts_prop_instance = Contacts_Prop.objects.get(property_name=property_name)
    SyncDeliveryService.do_sync_parameters(
        employee_instance,
        contacts_prop_instance,
        value=max_date,
        modified_by="sync_date_relations",
    )


def _sync_employee_operational_periods(employee_id: int) -> None:
    """Recalculates operational_periods for employee after FireRun changes"""
    if not employee_id:
        return

    RecordsService.set_operational_periods_for_all_employees(employee_id=employee_id)


@receiver(pre_save, sender=FireRun)
def track_employee_id_change(sender, instance, **kwargs):
    """Saves old employee_id before saving to handle changes"""
    if instance.pk:
        try:
            old_instance = FireRun.objects.get(pk=instance.pk)
            # Save old value in instance attribute for use in post_save
            instance._old_employee_id = old_instance.employee_id
        except FireRun.DoesNotExist:
            instance._old_employee_id = None
    else:
        instance._old_employee_id = None


@receiver(post_save, sender=FireRun)
def sync_date_relations(sender, instance, **kwargs):
    # changed: defer until commit; prevents in-transaction reads
    employee_id = instance.employee_id
    transaction.on_commit(lambda: _sync_employee_last_firerun_date(employee_id))

    # Recalculate operational_periods for current employee
    transaction.on_commit(
        lambda emp_id=employee_id: _sync_employee_operational_periods(emp_id)
    )

    # If employee_id changed, recalculate for old employee as well
    old_employee_id = getattr(instance, "_old_employee_id", None)
    if old_employee_id and old_employee_id != employee_id:
        transaction.on_commit(
            lambda emp_id=old_employee_id: _sync_employee_operational_periods(emp_id)
        )


@receiver(post_delete, sender=FireRun)
def sync_date_relations_on_delete(sender, instance, **kwargs):
    # changed: keep in sync on delete
    employee_id = instance.employee_id
    transaction.on_commit(lambda: _sync_employee_last_firerun_date(employee_id))

    # Recalculate operational_periods after deletion
    transaction.on_commit(
        lambda emp_id=employee_id: _sync_employee_operational_periods(emp_id)
    )
