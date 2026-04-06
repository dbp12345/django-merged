from celery import shared_task
from django.conf import settings
from django.db import transaction

from company.models import Employees_Parameters
from company.services.EmployeesService import get_employees_by_filter, EmployeesService
from privser.models import Custom_Fields, Contacts_Parameters
from privser.models import Contacts as ContactsPrivser
from synchronization.models import Sync_Delivery_Logs

@shared_task
def sync_employees_task(direction, employee_filter_id, selected_fields):
    employees_qs = get_employees_by_filter(employee_filter_id)
    # employees_qs = get_employees_by_filter(employee_filter_id)
    # employees_qs = Employees.objects.filter(email = "Test12@Automation.com")

    if direction == "django_to_privser":
        from synchronization.services.SyncDeliveryService import SyncDeliveryService
        from core.tasks import handle_sync_delivery_log_task
        for employee in employees_qs:
            # print("employee.email", employee.get_email)
            changed_properties_new = {}
            for custom_fields_id in selected_fields:
                custom_fields_instance = Custom_Fields.objects.filter(id=custom_fields_id).first()

                if custom_fields_instance:
                    # print("custom_fields_instance_privser_name", custom_fields_instance.privser_name)
                    # print("custom_fields_instance_privser_id", custom_fields_instance.privser_id)
                    contacts_prop_instance = custom_fields_instance.exchange_property
                    # print("contacts_prop_instance", contacts_prop_instance)
                    # print("employee", employee)
                    contacts_parameters_instance = Employees_Parameters.objects.filter(contacts_prop=contacts_prop_instance, employee=employee).first()
                    # print("contacts_parameters_instance", contacts_parameters_instance)


                    if contacts_parameters_instance:
                        changed_properties_new[contacts_prop_instance] = contacts_parameters_instance.value

            for contacts_prop_obj, param_value in changed_properties_new.items():
                print("_____________", employee.get_email)
                print(contacts_prop_obj, param_value)



                # changed_parameters: dict = None,  # dict[Contacts_Prop, new_value]
                # old_parameters: dict = None,  # dict[Contacts_Prop, old_value]

                sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
                    employee=employee,
                    changed_parameters={contacts_prop_obj: param_value},
                    old_parameters={contacts_prop_obj: 'unknown'},
                    target_system=Sync_Delivery_Logs.TargetSystemChoices.PRIVSER,
                    modified_by="External Sync"
                )
                for sync_delivery_log_id in sync_delivery_log_ids:
                    if settings.DEBUG:
                        handle_sync_delivery_log_task.run(sync_delivery_log_id)
                    else:
                        transaction.on_commit(lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(sync_id))

    if direction == "privser_to_exc":
        from synchronization.services.SyncDeliveryService import SyncDeliveryService
        from core.tasks import handle_sync_delivery_log_task
        for employee in employees_qs:
            changed_properties_new = {}
            contact_privser_obj = ContactsPrivser.objects.filter(email=employee.email).first()
            if contact_privser_obj:
                for custom_fields_id in selected_fields:
                    custom_fields_instance = Custom_Fields.objects.filter(id=custom_fields_id).first()

                    if custom_fields_instance:
                        contacts_prop_instance = custom_fields_instance.exchange_property
                        contacts_parameters_instance = Contacts_Parameters.objects.filter(
                            name__in=[custom_fields_instance.privser_id, custom_fields_instance.privser_name],
                            contacts=contact_privser_obj
                        ).first()

                        if contacts_parameters_instance:
                            changed_properties_new[contacts_prop_instance] = contacts_parameters_instance.value


            employees_service = EmployeesService()
            employees_service.set_contact(employee_obj=employee)


            for contacts_prop_obj, param_value in changed_properties_new.items():
                # print("_____________")
                # print(employees_service.employee_obj)
                # print(contacts_prop_obj, param_value)
                employees_service.set_contact_parameters(contacts_prop_obj, param_value)

            employees_service.do_update_or_create_contact_parameters(modified_by="External Sync")
            changed_parameters = employees_service.get_all_changed_parameters_obj()
            old_parameters = employees_service.get_old_parameters_obj()

            # print("employees_service.get_contact_parameters", employees_service.get_contact_parameters())
            # print("changed_parameters", changed_parameters)
            # print("old_parameters", old_parameters)

            # sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
            #     employee=employee,
            #     changed_parameters=changed_parameters,
            #     old_parameters=old_parameters,
            #     target_system=Sync_Delivery_Logs.TargetSystemChoices.PRIVSER,
            #     modified_by="External Sync"
            # )
            # for sync_delivery_log_id in sync_delivery_log_ids:
            # from core.tasks import handle_sync_delivery_log_task
            #     if settings.DEBUG:
            #         handle_sync_delivery_log_task.run(sync_delivery_log_id)
            #     else:
            #         handle_sync_delivery_log_task.delay(sync_delivery_log_id)

            sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
                employee=employee,
                changed_parameters=changed_parameters,
                old_parameters=old_parameters,
                target_system=Sync_Delivery_Logs.TargetSystemChoices.EXCHANGE,
                modified_by="External Sync"
            )
            for sync_delivery_log_id in sync_delivery_log_ids:
                if settings.DEBUG:
                    handle_sync_delivery_log_task.run(sync_delivery_log_id)
                else:
                    handle_sync_delivery_log_task.delay(sync_delivery_log_id) #good

    # if direction == "privser_to_exc_OLD":
    #     for emp in employees_qs:
    #         changed_properties_new = {}
    #         contact_privser_obj = ContactsPrivser.objects.filter(email=emp.email).first()
    #         if contact_privser_obj:
    #             for custom_fields_id in selected_fields:
    #                 custom_fields_instance = Custom_Fields.objects.filter(id=custom_fields_id).first()
    #
    #                 if custom_fields_instance:
    #                     # print("contact_privser_obj.id", contact_privser_obj.id)
    #                     # print("custom_fields_instance.privser_name", custom_fields_instance.privser_name)
    #                     contacts_parameters_instance = Contacts_Parameters.objects.filter(
    #                         name__in=[custom_fields_instance.privser_id, custom_fields_instance.privser_name],
    #                         contacts=contact_privser_obj).first()
    #                     if contacts_parameters_instance:
    #                         changed_properties_new[custom_fields_instance.privser_name] = contacts_parameters_instance.value
    #                         # changed_properties_new[contacts_prop_instance.property_name] = contacts_parameters_instance.value
    #
    #             # print(contact_privser_obj.id)
    #             # print(changed_properties_new)
    #             SyncInstantService.handle_changed_properties_privser(contact_privser_obj=contact_privser_obj, changed_properties_privser=changed_properties_new)

    # if direction == "exc_to_privser":
    #     for emp in employees_qs:
    #         changed_properties_new = {}
    #         contact_privser_obj = ContactsPrivser.objects.filter(email=emp.email).first()
    #         if contact_privser_obj:
    #             for custom_fields_id in selected_fields:
    #                 custom_fields_instance = Custom_Fields.objects.filter(id=custom_fields_id).first()
    #
    #                 if custom_fields_instance:
    #                     # print("custom_fields_instance_privser_name", custom_fields_instance.privser_name)
    #                     # print("custom_fields_instance_privser_id", custom_fields_instance.privser_id)
    #                     contacts_prop_instance = custom_fields_instance.exchange_property
    #                     contacts_parameters_instance = Employees_Parameters.objects.filter(contacts_prop=contacts_prop_instance, employee=emp).first()
    #
    #                     if contacts_parameters_instance:
    #                         changed_properties_new[contacts_prop_instance] = contacts_parameters_instance.value
    #
    #             # print(changed_properties_new)
    #             SyncInstantService.handle_changed_properties_exchange(employee_obj=emp, changed_properties_exchange=changed_properties_new)


# def get_employees_by_filter(filter_id: int):
#     from company.views.EmployeesParametersAjaxView import (
#         get_relation_param_to_annotation,
#         get_employees_all_prefetch_related,
#         parse_or_filter_groups,
#         apply_all_filters_with_or
#     )
#
#     filter_obj = Saved_Filter.objects.get(id=filter_id)
#     display_fields = filter_obj.columns
#     params = filter_obj.params
#
#     relation_map = get_relation_param_to_annotation()
#
#     employees_qs = get_employees_all_prefetch_related().order_by("-updated_at")
#
#     for field in display_fields:
#         if field in relation_map and relation_map[field]:
#             alias, annotation = relation_map[field]
#             employees_qs = employees_qs.annotate(**{alias: annotation})
#
#     or_filter_groups, group_logic_map = parse_or_filter_groups(params.items())
#     employees_qs = apply_all_filters_with_or(employees_qs, or_filter_groups, group_logic_map)
#
#     return employees_qs
