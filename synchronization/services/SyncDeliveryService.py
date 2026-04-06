from django.db import transaction

from company.models import Employees
from django.conf import settings

from company.services.EmployeesService import EmployeesService
from core.exceptions import StopTask
from core.services.SanitazerService import SanitazerService
from core.task_toggle import is_task_enabled
from exchange.models import Contacts_Prop
from privser.models import Custom_Fields, Contacts
from privser.services.PrivserAPI2Service import PrivserAPI2Service
from synchronization.models import Sync_Delivery_Logs
from core.tasks import update_exc_contact_by_email_with_data_task, update_privser_contact_task


class SyncDeliveryService:

    @staticmethod
    def add_sync_delivery_log(
            employee: Employees,
            changed_parameters: dict = None,  # dict[Contacts_Prop, new_value]
            old_parameters: dict = None,  # dict[Contacts_Prop, old_value]
            target_system=None,
            modified_by=None
    ):
        """
        :param employee: Employees instance
        :param changed_parameters: dict[Contacts_Prop, new_value]
        :param old_parameters: dict[Contacts_Prop, old_value]
        :param target_system: str
        :param modified_by: str
        """
        ids = []
        if changed_parameters is None:
            changed_parameters = {}
        if old_parameters is None:
            old_parameters = {}
        if not changed_parameters:
            return []

        for contacts_prop_instance, new_value in changed_parameters.items():
            old_value = old_parameters.get(contacts_prop_instance)

            # custom_fields = None
            # custom_fields_main_field = None
            # custom_fields_privser_name = None
            # if target_system == Sync_Delivery_Logs.TargetSystemChoices.PRIVSER:
            #     custom_fields = Custom_Fields.objects.filter(exchange_property=contacts_prop_instance).first()
            #     if custom_fields:
            #         custom_fields_main_field = custom_fields.main_field
            #         custom_fields_privser_name = custom_fields.privser_name

            if contacts_prop_instance.property_type == Contacts_Prop.TypeChoices.ARRAY:
                new_value = ",".join(new_value)

            log = Sync_Delivery_Logs.objects.create(
                email=employee.email,
                employee=employee,
                contacts_prop=contacts_prop_instance,
                # privser_custom_fields=custom_fields,
                contacts_prop_name=contacts_prop_instance.property_name,
                # privser_custom_fields_main_field=custom_fields_main_field,
                # privser_custom_fields_name=custom_fields_privser_name,
                old_value=old_value,
                new_value=new_value,
                target_system=target_system,
                body={},
                modified_by=modified_by,
                status_code=Sync_Delivery_Logs.StatusCode.NEW.value
            )
            ids.append(log.id)

        return ids

    @staticmethod
    def handle_sync_delivery_log(sync_delivery_logs_id):
        log_instance = Sync_Delivery_Logs.objects.get(id=sync_delivery_logs_id)

        log_i_id = log_instance.id
        log_i_email = log_instance.email
        log_i_target_system = log_instance.target_system
        log_i_new_value = log_instance.new_value
        # log_i_contacts_prop_name = log_instance.contacts_prop_name
        log_i_contacts_prop_name = log_instance.contacts_prop.property_name

        if log_i_target_system == Sync_Delivery_Logs.TargetSystemChoices.EXCHANGE:
            if is_task_enabled("update_exc_contact_by_email_with_data_task"):
                if settings.DEBUG:
                    update_exc_contact_by_email_with_data_task.run(
                        email=log_i_email,
                        data={log_i_contacts_prop_name: log_i_new_value},
                        log_id=log_i_id,
                    )
                else:
                    # update_exc_contact_by_email_with_data_task.delay(
                    #     email=log_i_email,
                    #     data={log_i_contacts_prop_name: log_i_new_value},
                    #     log_id=log_i_id,
                    # )
                    update_exc_contact_by_email_with_data_task.apply_async(
                        kwargs={
                            "email": log_i_email,
                            "data": {log_i_contacts_prop_name: log_i_new_value},
                            "log_id": log_i_id,
                        },
                        queue="exchange_throttled"
                    )
        elif log_i_target_system == Sync_Delivery_Logs.TargetSystemChoices.PRIVSER:

            # sync_main_fields_privser_dict = {'dateOfBirth': '2011-01-11 11:00:00', 'firstName': 'Test-8fn'}
            # sync_custom_fields_privser_dict = {'04rXHtJ3rctIgAXu39aM': 'Test-114', 'PQQjv7xlRat4kyGjGZlc': 'Test-8444', '7uSOnJcfst4XQski7gGU': '1'}
            # {
            #   "id": "6dvNaf7VhkQ9snc5vnjJ",
            #   "key": "my_custom_field",
            #   "field_value": "9039160788"
            # }

            # notes = sync_main_fields_privser_dict.pop("Notes", None)
            # contact_privser_id = contact_privser_obj.contact_id
            # if notes:
            #     response = privser_api2_service.create_note(
            #         contact_id=contact_privser_id,
            #         body=notes
            #     )
            #     note_id_new = response.get("note").get("id")
            #
            #     response = privser_api2_service.get_all_notes(contact_privser_id)
            #     from privser.services.PrivserService import PrivserService
            #     privser_service = PrivserService()
            #     ids = privser_service.all_notes_ids_from_res(response)
            #     ids.remove(note_id_new)
            #     for note_id in ids:
            #         privser_api2_service.delete_note(contact_id=contact_privser_id, note_id=note_id)

            privser_contact_id = None
            try:
                try:
                    privser_contact_id = Contacts.objects.get(email=log_i_email).contact_id
                except Contacts.DoesNotExist:
                    privser_api2_service = PrivserAPI2Service()
                    contact_response = privser_api2_service.get_contacts_by_email(email=log_i_email)
                    if contact_response["status"] == "one":
                        # contact_id = contact_response["contact"][0]["id"]
                        contact_id = next(
                            (c.get("id") for c in (contact_response or {}).get("contact", []) if "id" in c),
                            None
                        )
                        if contact_id:
                            contacts_obj, created = Contacts.objects.update_or_create(
                                email=log_i_email,
                                contact_id=contact_id,
                                defaults={
                                    # "date_updated": date_updated,
                                    # "last_activity": last_activity,
                                }
                            )
                            privser_contact_id = contacts_obj.contact_id
                    elif contact_response["status"] == "none":
                        response_privser = privser_api2_service.create_contact(
                            email=log_i_email
                        )
                        contact_id = (response_privser or {}).get("contact", {}).get("id")

                        if contact_id:
                            contacts_obj, created = Contacts.objects.update_or_create(
                                email=log_i_email,
                                contact_id=contact_id,
                                defaults={
                                    # "date_updated": date_updated,
                                    # "last_activity": last_activity,
                                }
                            )
                            privser_contact_id = contacts_obj.contact_id
                    elif contact_response["status"] == "multiple":
                        raise StopTask("More than one contact found with this email.", status_code=Sync_Delivery_Logs.StatusCode.MULTIPLE_CONTACT_LINK.value)

                except Contacts.MultipleObjectsReturned:
                    raise ValueError(f"Multiple contacts found for email: {log_i_email}")
                custom_fields = Custom_Fields.objects.filter(exchange_property=log_instance.contacts_prop).first()
            except Exception as e:
                raise StopTask(str(e), status_code=Sync_Delivery_Logs.StatusCode.NO_CONTACT_LINK.value)

            if not custom_fields:
                raise StopTask("Custom fields no matches", status_code=Sync_Delivery_Logs.StatusCode.NO_DATA_LINKS.value)

            if not privser_contact_id:
                raise StopTask("privser_contact_id not resolved", status_code=Sync_Delivery_Logs.StatusCode.NO_CONTACT_LINK.value)

            log_instance.privser_custom_fields = custom_fields
            log_instance.privser_custom_fields_name = custom_fields.privser_name
            log_instance.save()

            sync_main_fields_privser_dict = {}
            sync_custom_fields_privser_dict = []

            sanitized_value = SanitazerService.check_datetime_str_to_str(
                input_string=log_i_new_value,
                output_format="%Y-%m-%d"
            )
            if custom_fields.main_field:
                sync_main_fields_privser_dict[custom_fields.privser_name] = sanitized_value
            else:
                sync_custom_fields_privser_dict.append({
                    "id": custom_fields.privser_id,
                    "key": custom_fields.privser_name,
                    "field_value": sanitized_value
                })

            if settings.DEBUG:
                update_privser_contact_task.run(
                    contact_id=privser_contact_id,
                    main_fields=sync_main_fields_privser_dict,
                    custom_fields_list=sync_custom_fields_privser_dict,
                    log_id=log_i_id,
                )
            else:
                update_privser_contact_task.delay(
                    contact_id=privser_contact_id,
                    main_fields=sync_main_fields_privser_dict,
                    custom_fields_list=sync_custom_fields_privser_dict,
                    log_id=log_i_id,
                )

    @staticmethod
    def do_sync_parameters(employee: "Employees", contacts_prop_instance: "Contacts_Prop", value=None, modified_by=None, privser=True, exchange=True):
        from core.tasks import handle_sync_delivery_log_task
        employees_service = EmployeesService()
        employees_service.set_contact(employee_obj=employee)
        employees_service.set_contact_parameters(contacts_prop_instance, value)

        employees_service.do_update_or_create_contact_parameters(modified_by=modified_by)
        changed_parameters = employees_service.get_all_changed_parameters_obj()
        old_parameters = employees_service.get_old_parameters_obj()

        if privser:
            sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
                employee=employee,
                changed_parameters=changed_parameters,
                old_parameters=old_parameters,
                target_system=Sync_Delivery_Logs.TargetSystemChoices.PRIVSER,
                modified_by=modified_by
            )
            for sync_delivery_log_id in sync_delivery_log_ids:
                if settings.DEBUG:
                    handle_sync_delivery_log_task.run(sync_delivery_log_id)
                else:
                    transaction.on_commit(lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(sync_id))
                    # handle_sync_delivery_log_task.delay(sync_delivery_log_id)


        if exchange:
            sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
                employee=employee,
                changed_parameters=changed_parameters,
                old_parameters=old_parameters,
                target_system=Sync_Delivery_Logs.TargetSystemChoices.EXCHANGE,
                modified_by=modified_by
            )
            for sync_delivery_log_id in sync_delivery_log_ids:
                if settings.DEBUG:
                    handle_sync_delivery_log_task.run(sync_delivery_log_id)
                else:
                    transaction.on_commit(lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(sync_id))
                    # handle_sync_delivery_log_task.delay(sync_delivery_log_id)
