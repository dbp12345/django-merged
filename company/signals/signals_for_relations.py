from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

from company.models.Employees import Student, Course, Employees, TrainingClass
from company.services.EmployeesService import (
    find_property_name_by_instance,
    EmployeesService,
)
from exchange.models import Contacts_Prop

from typing import Optional
from datetime import date
from django.db.models import Max

from synchronization.services.SyncDeliveryService import SyncDeliveryService


# @receiver(post_save, sender=FireCrew)
# @receiver(post_save, sender=FireCrewHistory)
# @receiver(post_save, sender=EmergencyContact)
# @receiver(post_save, sender=MSPA)
# @receiver(post_save, sender=IdentificationDocuments)
# @receiver(post_save, sender=DispatchingStatus)
# @receiver(post_save, sender=CompanyManifest)
# @receiver(post_save, sender=DrugTest)
# @receiver(post_save, sender=NomexCheckOut)
# @receiver(post_save, sender=NomexCheckIn)
# @receiver(post_save, sender=EmploymentPacket)
# @receiver(post_save, sender=IQCCard)
# @receiver(post_save, sender=Interaction)
# @receiver(post_save, sender=TaskBook)
# @receiver(post_save, sender=Availability)
# @receiver(post_save, sender=CurrentAssigned)
# @receiver(post_save, sender=Notes)
# @receiver(post_save, sender=TrainingType)
# @receiver(post_save, sender=Course)
# @receiver(post_save, sender=TrainingClass)
# @receiver(post_save, sender=Student)
# @receiver(post_save, sender=RateOfPay)
# @receiver(post_save, sender=Fire)
# @receiver(post_save, sender=Crew)
# @receiver(post_save, sender=FireRun)
# @receiver(post_save, sender=CrewTimeReport)
# @receiver(post_save, sender=Evaluation)
# @receiver(post_save, sender=DayOnFire)
def sync_emp_relations(sender, instance, **kwargs):
    # print("sync_emp_relations(), instance", instance)
    friendly_name, instance_value = find_property_name_by_instance(instance)
    # print("sync_emp_relations(), friendly_name, instance_value", friendly_name, instance_value)
    if friendly_name:
        from core.tasks import handle_sync_delivery_log_task
        from synchronization.models import Sync_Delivery_Logs

        contacts_prop_instance = Contacts_Prop.objects.get(property_name=friendly_name)

        employees_service = EmployeesService()
        employees_service.set_contact(employee_obj=instance.employee)
        employees_service.set_contact_parameters(contacts_prop_instance, instance_value)

        employees_service.do_update_or_create_contact_parameters(
            modified_by="signals_for_relations"
        )
        changed_parameters = employees_service.get_all_changed_parameters_obj()
        old_parameters = employees_service.get_old_parameters_obj()

        sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
            employee=instance.employee,
            changed_parameters=changed_parameters,
            old_parameters=old_parameters,
            target_system=Sync_Delivery_Logs.TargetSystemChoices.PRIVSER,
            modified_by="signals_for_relations",
        )
        for sync_delivery_log_id in sync_delivery_log_ids:
            if settings.DEBUG:
                handle_sync_delivery_log_task.run(sync_delivery_log_id)
            else:
                transaction.on_commit(
                    lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(
                        sync_id
                    )
                )
                # handle_sync_delivery_log_task.delay(sync_delivery_log_id)

        sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
            employee=instance.employee,
            changed_parameters=changed_parameters,
            old_parameters=old_parameters,
            target_system=Sync_Delivery_Logs.TargetSystemChoices.EXCHANGE,
            modified_by="signals_for_relations",
        )
        for sync_delivery_log_id in sync_delivery_log_ids:
            if settings.DEBUG:
                handle_sync_delivery_log_task.run(sync_delivery_log_id)
            else:
                transaction.on_commit(
                    lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(
                        sync_id
                    )
                )
                # handle_sync_delivery_log_task.delay(sync_delivery_log_id)

            # if sender == CompanyManifest:
            #     from core.services.ManifestService import ManifestService
            #     transaction.on_commit(
            #         lambda: ManifestService.update_is_manifested_flags_from_all_dates(
            #             employee_id=instance.employee.id
            #         )
            #     )


# @receiver(post_delete, sender=FireCrew)
# @receiver(post_delete, sender=FireCrewHistory)
# @receiver(post_delete, sender=EmergencyContact)
# @receiver(post_delete, sender=MSPA)
# @receiver(post_delete, sender=IdentificationDocuments)
# @receiver(post_delete, sender=DispatchingStatus)
# @receiver(post_delete, sender=CompanyManifest)
# @receiver(post_delete, sender=DrugTest)
# @receiver(post_delete, sender=NomexCheckOut)
# @receiver(post_delete, sender=NomexCheckIn)
# @receiver(post_delete, sender=EmploymentPacket)
# @receiver(post_delete, sender=IQCCard)
# @receiver(post_delete, sender=Interaction)
# @receiver(post_delete, sender=TaskBook)
# @receiver(post_delete, sender=Availability)
# @receiver(post_delete, sender=CurrentAssigned)
# @receiver(post_delete, sender=Notes)
# @receiver(post_delete, sender=TrainingType)
# @receiver(post_delete, sender=Course)
# @receiver(post_delete, sender=TrainingClass)
# @receiver(post_delete, sender=Student)
# @receiver(post_delete, sender=RateOfPay)
# @receiver(post_delete, sender=Fire)
# @receiver(post_delete, sender=Crew)
# @receiver(post_delete, sender=FireRun)
# @receiver(post_delete, sender=CrewTimeReport)
# @receiver(post_delete, sender=Evaluation)
# @receiver(post_delete, sender=DayOnFire)
def delete_emp_relations(sender, instance, **kwargs):
    result = find_property_name_by_instance(instance)
    if not result:
        return

    friendly_name, _ = result
    if not friendly_name:
        return

    from core.tasks import handle_sync_delivery_log_task
    from synchronization.models import Sync_Delivery_Logs
    from synchronization.services.SyncDeliveryService import SyncDeliveryService

    contacts_prop_instance = Contacts_Prop.objects.get(property_name=friendly_name)

    employees_service = EmployeesService()
    employees_service.set_contact(employee_obj=instance.employee)
    employees_service.set_contact_parameters(contacts_prop_instance, None)

    employees_service.do_update_or_create_contact_parameters(
        modified_by="signals_for_relations"
    )
    changed_parameters = employees_service.get_all_changed_parameters_obj()
    old_parameters = employees_service.get_old_parameters_obj()

    sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
        employee=instance.employee,
        changed_parameters=changed_parameters,
        old_parameters=old_parameters,
        target_system=Sync_Delivery_Logs.TargetSystemChoices.PRIVSER,
        modified_by="signals_for_relations",
    )
    for sync_delivery_log_id in sync_delivery_log_ids:
        if settings.DEBUG:
            handle_sync_delivery_log_task.run(sync_delivery_log_id)
        else:
            transaction.on_commit(
                lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(
                    sync_id
                )
            )
            # handle_sync_delivery_log_task.delay(sync_delivery_log_id)

    sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
        employee=instance.employee,
        changed_parameters=changed_parameters,
        old_parameters=old_parameters,
        target_system=Sync_Delivery_Logs.TargetSystemChoices.EXCHANGE,
        modified_by="signals_for_relations",
    )
    for sync_delivery_log_id in sync_delivery_log_ids:
        if settings.DEBUG:
            handle_sync_delivery_log_task.run(sync_delivery_log_id)
        else:
            transaction.on_commit(
                lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(
                    sync_id
                )
            )
            # handle_sync_delivery_log_task.delay(sync_delivery_log_id)

    # if sender == CompanyManifest:
    #     # перенес это на изменение параметров...
    #     from core.services.ManifestService import ManifestService

    #     transaction.on_commit(
    #         lambda: ManifestService.update_is_manifested_flags_from_all_dates(
    #             employee_id=instance.employee.id
    #         )
    #     )


# @receiver(post_save, sender=Availability)
# def handle_availability(sender, instance, **kwargs):
# logic for Availabilty Object
# we dont always sync every field into the object
# depending on the item selected we sync different fields
#
# for all items on list:
# date of change is always today
#
# if not currently available
# sync "Date of Expected Future Change Field" -> Available for Dispatch
# -sync "Current Location" -> Current State Dispatching From
# =sync:  date of change = today
# -sync Travel Time
#
# If changed to
# Available
# -Sync ready date = today in excange, djanga and privser -> Ready
# -sync "Current Location" -> Current State Dispatching From
# =sync:  date of change = today
# -sync Travel Time
#
# Injured
# -sync "Date of Expected Future Change Field" -> Available for Dispatch
# -sync "Current Location" -> Current State Dispatching From
# =sync:  date of change = today
# -sync Travel Time
#
# All other selection on list
# =sync:  date of change = today

# TODO это зацикливает историю. Надо перенести на параметры.
# if instance.availability_status in ("Not Currently Available", "Injured"):
#     updated_data = {
#         Contacts_Prop.objects.get(property_name="Available for Dispatch"): instance.date_of_expected_future_change,
#         Contacts_Prop.objects.get(property_name="Ready"): None
#     }
#     update_employee_parameters_raw(employee=instance.employee, parameters=updated_data)
#     # print("Available for Dispatch::::::::::::::::", instance.date_of_expected_future_change)
# if instance.availability_status in ("Available",):
#     updated_data = {
#         Contacts_Prop.objects.get(property_name="Available for Dispatch"): None,
#         Contacts_Prop.objects.get(property_name="Ready"): instance.date_of_expected_future_change
#     }
#     update_employee_parameters_raw(employee=instance.employee, parameters=updated_data)
#     # print("Ready::::::::::::::::", instance.date_of_expected_future_change)


# Делаем небольшой хардкод для передачи параметра из обьекта Студента
@receiver([post_save, post_delete], sender=Student)
def sync_student_relations(sender, instance, **kwargs):
    # print("sync_student_relations(), sender", sender)
    # print("sync_student_relations(), instance", instance)
    # print("sync_student_relations(), instance.training_class", instance.training_class)
    # print(
    #     "sync_student_relations(), instance.training_class.date",
    #     instance.training_class.date,
    # )
    # print(
    #     "sync_student_relations(), instance.training_class.course",
    #     instance.training_class.course,
    # )
    # print(
    #     "sync_student_relations(), instance.training_class.course.training_type",
    #     instance.training_class.course.training_type,
    # )
    # print(
    #     "sync_student_relations(), instance.training_class.course.training_type.name",
    #     instance.training_class.course.training_type.name,
    # )

    try:
        course_name = instance.training_class.course.training_type.name
        # course_date = instance.training_class.date
    except AttributeError:
        # course_name = None
        return
        # course_date = None

    course_date = get_latest_training_date_for_employee_and_course(
        instance.training_class.course, instance.employee
    )
    # print("sync_student_relations(), course_date", course_date)
    # print("sync_student_relations(), course_name", course_name)

    dict_course = {
        "RT-130": "Current Refresher Date",
        "RT-130 Webinar": "RT-130 Webinar 2025",
        "S-130": "S130",
        "S-130 Online Component": "S130 Online Component",
        "S-131": "S-131",
        "S-190": "S190",
        "S-190 Webinar": "S-190 Webinar",
        "S-212": "S-212",
        "S-230": "S-230",
        "S-290": "S-290",
        "L-180": "L180",
        "L-180 Webinar": "L-180 Webinar",
        "IS-100": "ICS100",
        "IS-200": "IS-200.b",
        "IS-700": "I700",
        "M-410": "M-410",
        "Pack Test": "Current Pack Test Date",
        "Driver Training": "Driver Training",
    }

    property_name = dict_course.get(course_name, None)

    # print("sync_student_relations(), property_name", property_name)
    if property_name:
        contacts_prop_instance = Contacts_Prop.objects.get(property_name=property_name)
        SyncDeliveryService.do_sync_parameters(
            instance.employee,
            contacts_prop_instance,
            value=course_date,
            modified_by="sync_student_relations",
        )


# возвращает дату
def get_latest_training_date_for_employee_and_course(
    course: Course, employee: Employees
) -> Optional[date]:
    result = Student.objects.filter(
        employee=employee,
        training_class__course=course,
        training_class__date__isnull=False,
    ).aggregate(latest=Max("training_class__date"))
    return result["latest"]


# возвращает сам объект TrainingClass
def get_latest_training_class_for_employee_and_course(
    course: Course, employee: Employees
) -> Optional[TrainingClass]:
    return (
        TrainingClass.objects.filter(
            course=course, student_entries__employee=employee, date__isnull=False
        )
        .order_by("-date")
        .first()
    )
