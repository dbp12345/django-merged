from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Max
from django.db import transaction

from company.models import DayOnFire, Employees
from exchange.models import Contacts_Prop

from synchronization.services.SyncDeliveryService import SyncDeliveryService


def _sync_employee_last_dof_date(employee_id: int) -> None:
    if not employee_id:
        return
    max_date = (
        DayOnFire.objects
        .filter(fire_run__employee_id=employee_id)
        .exclude(date__isnull=True)
        .aggregate(d=Max("date"))["d"]
    )

    if not max_date:
        return

    employee_instance = Employees.objects.filter(id=employee_id).first()

    if not employee_instance:
        return

    property_name = "Last day on fire"
    contacts_prop_instance = Contacts_Prop.objects.get(property_name=property_name)
    SyncDeliveryService.do_sync_parameters(employee_instance, contacts_prop_instance, value=max_date, modified_by="sync_date_relations")


@receiver(post_save, sender=DayOnFire)
def sync_date_relations(sender, instance, **kwargs):
    # changed: defer until commit; prevents weirdness with in-transaction reads
    employee_id = instance.fire_run.employee_id if instance.fire_run_id else None
    transaction.on_commit(lambda: _sync_employee_last_dof_date(employee_id))


@receiver(post_delete, sender=DayOnFire)
def sync_date_relations_on_delete(sender, instance, **kwargs):
    # changed: keep в синхроне при удалении
    employee_id = instance.fire_run.employee_id if instance.fire_run_id else None
    transaction.on_commit(lambda: _sync_employee_last_dof_date(employee_id))
