import time
import traceback

from django.conf import settings

from company.models import Employees
from company.services.EmployeesService import EmployeesService
from core.services.SanitazerService import SanitazerService
from company.models.EmployeesParameters import Employees_Parameters
from exchange.models import Contacts_Prop
from privser.models.ContactsParameters import Contacts_Parameters as Contacts_Parameters_Privser
from privser.models.CustomFields import Custom_Fields
from privser.services.PrivserAPI2Service import PrivserAPI2Service
from synchronization.models import Sync_Parameters_Logs
from privser.models import Contacts as ContactsPrivser
from synchronization.models.SyncParametersLogs import System


class SyncInstantService:

    @staticmethod
    # @transaction.atomic
    def handle_changed_properties_exchange(
            employee_obj,
            changed_properties_exchange: dict = None
    ):
        """
        :param employee_obj:
        :param changed_properties_exchange: [key: exchange.Contacts_Prop, value]
        :return:
        """
        if changed_properties_exchange is None:
            changed_properties_exchange = {}
        email = employee_obj.email
        # contact_privser_obj = ContactsPrivser.objects.get(email=email)
        contact_privser_obj = ContactsPrivser.objects.filter(email=email).first()
        if not contact_privser_obj:
            print(f"ContactsPrivser matching query does not exist. Email: '{email}'")
            import logging
            logger = logging.getLogger("my_log")
            logger.error(
                f"ContactsPrivser matching query does not exist. Email: '{email}'\n"
            )
            return
            raise Exception(f"ContactsPrivser matching query does not exist. Email: '{email}'")

        if changed_properties_exchange:
            # -=
            body_data = {
                str(key): value
                for key, value in changed_properties_exchange.items()
            }
            Sync_Parameters_Logs.objects.create(
                email=email,
                employee=employee_obj,
                contact_privser=contact_privser_obj,
                source_system=System.exchange.name,
                target_system=System.privser.name,
                body=body_data,
                removed=True,
                status_code=Sync_Parameters_Logs.StatusCode.LOG
            )
            # =-
            sync_logs_obj_list = []
            for key, value in changed_properties_exchange.items():
                custom_fields = list(
                    Custom_Fields.objects.filter(exchange_property=key).exclude(exchange_property__isnull=True)
                )

                sync_logs_obj = Sync_Parameters_Logs.objects.create(
                    email=email,
                    employee=employee_obj,
                    property_name=key.property_name,
                    new_value=value,
                    contact_privser=contact_privser_obj,
                    source_system=System.exchange.name,
                    target_system=System.privser.name,
                    status_code=Sync_Parameters_Logs.StatusCode.NEW
                )
                error = []
                if not custom_fields:
                    sync_logs_obj.body = {"error": f"Custom fields {key.property_name} not matched/linked"}
                    sync_logs_obj.status_code = sync_logs_obj.StatusCode.ERROR
                elif len(custom_fields) > 1:
                    sync_logs_obj.body = {"error": f"Custom fields {key.property_name} found multiple matches/links"}
                    sync_logs_obj.status_code = sync_logs_obj.StatusCode.ERROR
                else:
                    custom_fields_obj_first = custom_fields[0]
                    try:
                        employees_parameters_obj = Employees_Parameters.objects.get(
                            employee=employee_obj,
                            contacts_prop=custom_fields_obj_first.exchange_property,
                        )
                        # sync_logs_obj.property_name = custom_fields_obj_first.exchange_property.property_name
                        exchange_modified_by_from_db = employees_parameters_obj.modified_by
                        exchange_value_from_db = employees_parameters_obj.value
                        exchange_datetime_from_db = employees_parameters_obj.updated_at
                    except Employees_Parameters.DoesNotExist:
                        exchange_modified_by_from_db = None
                        exchange_value_from_db = None
                        exchange_datetime_from_db = None
                    except Exception as e:
                        error.append(traceback.format_exc())
                        # error.append(str(e))  # ["Employees_Parameters matching query does not exist."]
                        exchange_modified_by_from_db = None
                        exchange_value_from_db = None
                        exchange_datetime_from_db = None

                    try:
                        if contact_privser_obj:
                            contacts_parameters_privser_obj = Contacts_Parameters_Privser.objects.get(
                                contacts=contact_privser_obj,
                                name__in=[custom_fields_obj_first.privser_name, custom_fields_obj_first.privser_id],
                            )
                            privser_value_from_db = contacts_parameters_privser_obj.value
                            privser_datetime_from_db = contacts_parameters_privser_obj.updated_at

                            exchange_property = custom_fields_obj_first.exchange_property
                            if privser_value_from_db and exchange_property and exchange_property.datetime_format:
                                privser_value_from_db = SanitazerService.convert_date_format_str(
                                    value=privser_value_from_db,
                                    from_format="%Y-%m-%d",
                                    output_format=exchange_property.datetime_format
                                )
                        else:
                            privser_value_from_db = None
                            privser_datetime_from_db = None
                            sync_logs_obj.status_code = sync_logs_obj.StatusCode.NO_RELATIONS
                    except Contacts_Parameters_Privser.DoesNotExist:
                        privser_value_from_db = None
                        privser_datetime_from_db = None
                    except Exception as e:
                        error.append(traceback.format_exc())
                        # error.append(str(e))
                        privser_value_from_db = None
                        privser_datetime_from_db = None

                    sync_logs_obj.modified_by = exchange_modified_by_from_db
                    sync_logs_obj.new_value = exchange_value_from_db
                    sync_logs_obj.new_value_updated = exchange_datetime_from_db
                    sync_logs_obj.old_value = privser_value_from_db
                    sync_logs_obj.old_value_updated = privser_datetime_from_db
                    sync_logs_obj.privser_custom_fields = custom_fields_obj_first

                    if custom_fields_obj_first.no_sync:
                        sync_logs_obj.status_code = sync_logs_obj.StatusCode.IGNORE

                if error:
                    if not sync_logs_obj.body:
                        sync_logs_obj.body = {}
                    sync_logs_obj.body.setdefault("errors", []).extend(error)
                    sync_logs_obj.status_code = sync_logs_obj.StatusCode.ERROR
                if sync_logs_obj.status_code == sync_logs_obj.StatusCode.NEW:
                    sync_logs_obj.status_code = sync_logs_obj.StatusCode.IN_PROGRESS
                    # sync_logs_obj.status_code = sync_logs_obj.StatusCode.TEST

                correct_status = SyncInstantService.get_correct_status(sync_logs_obj)
                sync_logs_obj.status_code = correct_status
                sync_logs_obj.save()
                sync_logs_obj_list.append(sync_logs_obj)

            SyncInstantService.update_remote_contacts(sync_logs_obj_list, employee_obj=employee_obj, contact_privser_obj=contact_privser_obj)
            # tod-o Положить в таски обработку статусов на раз в минуту на всякий случай.
            # tod-o Положить в таски обработку обновлений на раз в минуту на всякий случай.

    @staticmethod
    # @transaction.atomic
    def handle_changed_properties_privser(
            contact_privser_obj,
            changed_properties_privser: dict = None,
    ):
        if changed_properties_privser is None:
            changed_properties_privser = {}
        email = contact_privser_obj.email

        # Creating a new user in the system
        employee_obj = Employees.objects.filter(email=email).first()
        if not employee_obj:
            return #TODO2 Временно не создаем никого!
            from exchange.services.ExchangeService import ExchangeService
            from exchange.services.ExchangeUpdatesService import ExchangeUpdatesService
            exc_contact = ExchangeService.find_user_by_email(contact_exc_email=email)
            if not exc_contact:
                exc_contact = ExchangeService.create_contact_with_email(email_address=email) # создать в Exchange
            ExchangeUpdatesService.do_update_from_exchange(exc_contacts=[exc_contact], ignore_diff_properties=True) # чтобы создать у нас в системе
            employee_obj = Employees.objects.filter(email=email).first()


        changed_properties_privser.pop('lastActivity', None)
        changed_properties_privser.pop('date_updated', None)
        changed_properties_privser.pop('contactName', None)

        if changed_properties_privser:
            # -=
            body_data = {
                str(key): value
                for key, value in changed_properties_privser.items()
            }
            Sync_Parameters_Logs.objects.create(
                email=email,
                employee=employee_obj,
                contact_privser=contact_privser_obj,
                source_system=System.privser.name,
                target_system=System.exchange.name,
                body=body_data,
                removed=True,
                status_code=Sync_Parameters_Logs.StatusCode.LOG
            )
            # =-
            sync_logs_obj_list = []
            from django.db.models import Q
            # changed_properties_privser = PrivserService.update_keys_by_mapping(changed_properties_privser)
            for key, value in changed_properties_privser.items():
                custom_fields = list(
                    Custom_Fields.objects.filter(
                        Q(privser_id=key) | Q(privser_name=key)
                    )
                )

                try:
                    sync_logs_obj = Sync_Parameters_Logs.objects.create(
                        email=email,
                        employee=employee_obj,
                        property_name=key,
                        new_value=value,
                        contact_privser=contact_privser_obj,
                        source_system=System.privser.name,
                        target_system=System.exchange.name,
                        status_code=Sync_Parameters_Logs.StatusCode.NEW
                    )
                except Exception:
                    import re
                    def remove_non_bmp_chars(text):
                        if not isinstance(text, str):
                            return text
                        return re.sub(r"[\U00010000-\U0010FFFF]", "", text)

                    value = remove_non_bmp_chars(str(value))
                    sync_logs_obj = Sync_Parameters_Logs.objects.create(
                        email=email,
                        employee=employee_obj,
                        property_name=key,
                        new_value=value,
                        contact_privser=contact_privser_obj,
                        source_system=System.privser.name,
                        target_system=System.exchange.name,
                        status_code=Sync_Parameters_Logs.StatusCode.NEW
                    )

                error = []
                if not custom_fields:
                    sync_logs_obj.body = {"error": f"Custom fields {key} not matched/linked"}
                    sync_logs_obj.status_code = sync_logs_obj.StatusCode.ERROR
                elif len(custom_fields) > 1:
                    sync_logs_obj.body = {"error": f"Custom fields {key} found multiple matches/links"}
                    sync_logs_obj.status_code = sync_logs_obj.StatusCode.ERROR
                else:
                    custom_fields_obj_first = custom_fields[0]
                    try:
                        employees_parameters_obj = Employees_Parameters.objects.get(
                            employee=employee_obj,
                            contacts_prop=custom_fields_obj_first.exchange_property,
                        )
                        # sync_logs_obj.property_name = custom_fields_obj_first.privser_name
                        exchange_value_from_db = employees_parameters_obj.value
                        exchange_datetime_from_db = employees_parameters_obj.updated_at
                    except Employees_Parameters.DoesNotExist:
                        exchange_value_from_db = None
                        exchange_datetime_from_db = None
                    except Exception:
                        error.append(traceback.format_exc())
                        exchange_value_from_db = None
                        exchange_datetime_from_db = None

                    try:
                        contacts_parameters_privser_obj = Contacts_Parameters_Privser.objects.get(
                            contacts=contact_privser_obj,
                            name__in=[custom_fields_obj_first.privser_name, custom_fields_obj_first.privser_id],
                        )
                        privser_modified_by_from_db = contacts_parameters_privser_obj.modified_by
                        privser_value_from_db = contacts_parameters_privser_obj.value
                        privser_datetime_from_db = contacts_parameters_privser_obj.updated_at

                        exchange_property = custom_fields_obj_first.exchange_property
                        if privser_value_from_db and exchange_property and exchange_property.datetime_format:
                            privser_value_from_db = SanitazerService.convert_date_format_str(
                                value=privser_value_from_db,
                                from_format="%Y-%m-%d",
                                output_format=custom_fields_obj_first.exchange_property.datetime_format
                            )
                    except Contacts_Parameters_Privser.DoesNotExist:
                        privser_modified_by_from_db = None
                        privser_value_from_db = None
                        privser_datetime_from_db = None
                    except Exception as e:
                        error.append(traceback.format_exc())
                        # error.append(str(e))
                        privser_modified_by_from_db = None
                        privser_value_from_db = None
                        privser_datetime_from_db = None

                    sync_logs_obj.modified_by = privser_modified_by_from_db
                    sync_logs_obj.new_value = privser_value_from_db
                    sync_logs_obj.new_value_updated = privser_datetime_from_db
                    sync_logs_obj.old_value = exchange_value_from_db
                    sync_logs_obj.old_value_updated = exchange_datetime_from_db
                    sync_logs_obj.privser_custom_fields = custom_fields_obj_first

                    if custom_fields_obj_first.no_sync:
                        sync_logs_obj.status_code = sync_logs_obj.StatusCode.IGNORE

                if error:
                    if not sync_logs_obj.body:
                        sync_logs_obj.body = {}
                    sync_logs_obj.body.setdefault("errors", []).extend(error)
                    sync_logs_obj.status_code = sync_logs_obj.StatusCode.ERROR
                if sync_logs_obj.status_code == sync_logs_obj.StatusCode.NEW:
                    sync_logs_obj.status_code = sync_logs_obj.StatusCode.IN_PROGRESS
                    # sync_logs_obj.status_code = sync_logs_obj.StatusCode.TEST

                correct_status = SyncInstantService.get_correct_status(sync_logs_obj)
                sync_logs_obj.status_code = correct_status
                sync_logs_obj.save()
                sync_logs_obj_list.append(sync_logs_obj)

            SyncInstantService.update_remote_contacts(sync_logs_obj_list, employee_obj=employee_obj, contact_privser_obj=contact_privser_obj)

    @staticmethod
    def update_remote_contacts(sync_logs_obj_list, contact_privser_obj=None, employee_obj=None):
        # print("sync_logs_obj_list", sync_logs_obj_list)
        # return
        if not sync_logs_obj_list:
            return

        sync_main_fields_privser_dict = {}
        sync_custom_fields_privser_dict = []
        sync_parameters_exchange_dict = {}

        sync_logs_obj: Sync_Parameters_Logs
        for sync_logs_obj in sync_logs_obj_list:
            if sync_logs_obj.status_code != sync_logs_obj.StatusCode.IN_PROGRESS:
                continue

            if sync_logs_obj.target_system == System.privser.name and sync_logs_obj.privser_custom_fields:
                # exchange_value = SanitazerService.convert_date_format_str(
                #     value=sync_logs_obj.new_value,
                #     from_format=sync_logs_obj.privser_custom_fields.exchange_property.datetime_format,
                #     output_format="%Y-%m-%d"
                # )
                exchange_value = SanitazerService.check_datetime_str_to_str(
                    input_string=sync_logs_obj.new_value,
                    output_format="%Y-%m-%d"
                )
                if sync_logs_obj.privser_custom_fields.main_field:
                    sync_main_fields_privser_dict[sync_logs_obj.privser_custom_fields.privser_name] = exchange_value
                else:
                    sync_custom_fields_privser_dict.append({
                        "id": sync_logs_obj.privser_custom_fields.privser_id,
                        "key": sync_logs_obj.privser_custom_fields.privser_name,
                        "field_value": sync_logs_obj.new_value
                    })

            if sync_logs_obj.target_system == System.exchange.name and sync_logs_obj.privser_custom_fields:
                if sync_logs_obj.privser_custom_fields.exchange_property is None:
                    raise Exception(f"No link to Privser field name: '{sync_logs_obj.privser_custom_fields.privser_name}'")
                sync_parameters_exchange_dict[sync_logs_obj.privser_custom_fields.exchange_property.property_name] = sync_logs_obj.new_value
                continue

        # UPDATE IN PRIVSER:
        if (sync_main_fields_privser_dict or sync_custom_fields_privser_dict) and contact_privser_obj:
            contact_privser_id = contact_privser_obj.contact_id
            privser_api2_service = PrivserAPI2Service()

            # sync_main_fields_privser_dict = {'dateOfBirth': '2011-01-11 11:00:00', 'firstName': 'Test-8fn'}
            # sync_custom_fields_privser_dict = {'04rXHtJ3rctIgAXu39aM': 'Test-114', 'PQQjv7xlRat4kyGjGZlc': 'Test-8444', '7uSOnJcfst4XQski7gGU': '1'}
            # {
            #   "id": "6dvNaf7VhkQ9snc5vnjJ",
            #   "key": "my_custom_field",
            #   "field_value": "9039160788"
            # }

            # notes = sync_main_fields_privser_dict.pop("Notes", None)
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

            response_privser = privser_api2_service.update_contacts_fields(
                contact_privser_id,
                main_fields=sync_main_fields_privser_dict,
                custom_fields_list=sync_custom_fields_privser_dict
            )

            is_succeded = response_privser.get("succeded")
            if is_succeded is True:
                for sync_logs_obj in sync_logs_obj_list:
                    sync_logs_obj.body = {}
                    sync_logs_obj.status_code = sync_logs_obj.StatusCode.COMPLETED
                    sync_logs_obj.save(update_fields=["status_code", "updated_at", "body"])
            else:
                for sync_logs_obj in sync_logs_obj_list:
                    sync_logs_obj.status_code = sync_logs_obj.StatusCode.ERROR_API
                    sync_logs_obj.body= response_privser
                    sync_logs_obj.save(update_fields=["status_code", "body", "updated_at"])

            time.sleep(2)
            try:
                from privser.services.PrivserUpdatesService import PrivserUpdatesService
                PrivserUpdatesService.update_all_fields_from_contact_id(contact_privser_id, ignore_diff_properties=False)
            except Exception:
                import logging
                print("================ERROR update_remote_contacts================")
                print("contact_privser_id: ", contact_privser_id)
                print("sync_main_fields_privser_dict: ", sync_main_fields_privser_dict)
                logger = logging.getLogger("my_log")
                logger.error(
                    "\n================ ERROR update_remote_contacts ================\n"
                    f"contact_privser_id    : {contact_privser_id}\n"
                    f"sync_main_fields_privser_dict : {sync_main_fields_privser_dict}\n\n\n"
                )
        # print("sync_main_fields_privser_dict:", sync_main_fields_privser_dict)
        # print("sync_custom_fields_privser_dict:", sync_custom_fields_privser_dict)
        # print("sync_parameters_exchange_dict:", sync_parameters_exchange_dict)

        # UPDATE IN EXCHANGE:
        if sync_parameters_exchange_dict and employee_obj:
            employees_service = EmployeesService()
            employees_service.set_contact(employee_obj=employee_obj)

            response = {}
            updated_data = {}
            try:
                for property_name, new_property_value in sync_parameters_exchange_dict.items():
                    contacts_prop_obj = Contacts_Prop.objects.filter(property_name=property_name).first()
                    if contacts_prop_obj:
                        employees_service.set_contact_parameters(contacts_prop_obj, new_property_value)
                        updated_data[contacts_prop_obj.property_name] = new_property_value
                    else:
                        response[property_name] = "not found"

                employees_service.do_update_or_create_contact_parameters(modified_by="privser")
                changed_parameters = employees_service.get_all_changed_parameters_obj()

                print("sync_parameters_exchange_dict", sync_parameters_exchange_dict)
                print("changed_parameters", changed_parameters)

                # отправка в Exchange
                if updated_data:
                    from core.tasks import update_exc_contact_by_email_with_data_task
                    if settings.DEBUG:
                        update_exc_contact_by_email_with_data_task.run(email=employee_obj.email, data=sync_parameters_exchange_dict)
                    else:
                        update_exc_contact_by_email_with_data_task.delay(email=employee_obj.email, data=sync_parameters_exchange_dict)

                    for sync_logs_obj in sync_logs_obj_list:
                        if sync_logs_obj.status_code in (sync_logs_obj.StatusCode.IN_PROGRESS, sync_logs_obj.StatusCode.NEW):
                            sync_logs_obj.body = {}
                            sync_logs_obj.status_code = sync_logs_obj.StatusCode.COMPLETED
                            sync_logs_obj.save(update_fields=["status_code", "updated_at", "body"])
            except Exception:
                for sync_logs_obj in sync_logs_obj_list:
                    sync_logs_obj.body = traceback.format_exc()
                    sync_logs_obj.status_code = sync_logs_obj.StatusCode.ERROR_API
                    sync_logs_obj.save(update_fields=["status_code", "updated_at", "body"])



            # вроде тут мы отправляем в Эксч и потом от туда забираем, чтобы обновить в Джанго.
            # написал логику выше, эту нужно удалить !!!
            # Надо поменять это и обновлять в Джанго и потом отправть в Эксчендж
            # try:
            #     from exchange.services.ExchangeApiService import ExchangeApiService
            #     ExchangeApiService.update_exc_contact_by_email_with_data(email=employee_obj.email, data=sync_parameters_exchange_dict)
            # except Exception:
            #     import logging
            #     print("================ERROR update_remote_contacts================")
            #     print("User_id: ", employee_obj.contact_id)
            #     print("sync_parameters_exchange_dict: ", sync_parameters_exchange_dict)
            #     logger = logging.getLogger("my_log")
            #     logger.error(
            #         "\n================ ERROR update_remote_contacts ================\n"
            #         f"User_id    : {employee_obj.contact_id}\n"
            #         f"sync_parameters_exchange_dict : {sync_parameters_exchange_dict}\n\n\n"
            #     )
            # try:
            #     from exchange.services.ExchangeUpdatesService import ExchangeUpdatesService
            #     ExchangeUpdatesService.do_update_from_exchange_by_email(email=employee_obj.email, ignore_diff_properties=False)
            #     for sync_logs_obj in sync_logs_obj_list:
            #         if sync_logs_obj.status_code in (sync_logs_obj.StatusCode.IN_PROGRESS, sync_logs_obj.StatusCode.NEW):
            #             sync_logs_obj.body = {}
            #             sync_logs_obj.status_code = sync_logs_obj.StatusCode.COMPLETED
            #             sync_logs_obj.save(update_fields=["status_code", "updated_at", "body"])
            # except Exception:
            #     for sync_logs_obj in sync_logs_obj_list:
            #         sync_logs_obj.body = traceback.format_exc()
            #         sync_logs_obj.status_code = sync_logs_obj.StatusCode.ERROR_API
            #         sync_logs_obj.save(update_fields=["status_code", "updated_at", "body"])

    @staticmethod
    def get_correct_status(sync_logs_obj: Sync_Parameters_Logs):
        # if not isinstance(sync_logs_obj, Sync_Parameters_Logs):
        #     raise TypeError(f"Invalid object type: {type(sync_logs_obj).__name__}")

        if not sync_logs_obj.contact_privser or not sync_logs_obj.employee:
            return sync_logs_obj.StatusCode.NO_CONTACT_LINK

        if (
                not sync_logs_obj.privser_custom_fields or
                not sync_logs_obj.privser_custom_fields.exchange_property
        ):
            return sync_logs_obj.StatusCode.NO_PARAMETER_LINK

        if sync_logs_obj.privser_custom_fields.no_sync:
            return sync_logs_obj.StatusCode.IGNORE

        if sync_logs_obj.new_value is None or not sync_logs_obj.new_value:
            return sync_logs_obj.StatusCode.IGNORE

        if sync_logs_obj.privser_custom_fields.exchange_property.property_name == "MobilePhone":
            if SanitazerService.contains_phone(sync_logs_obj.old_value, sync_logs_obj.new_value):
                return sync_logs_obj.StatusCode.NO_CHANGES
        else:
            if (
                    (str(sync_logs_obj.old_value) or "").replace("\r", "").replace("\n", "").lower() ==
                    (str(sync_logs_obj.new_value) or "").replace("\r", "").replace("\n", "").lower()
            ):
                return sync_logs_obj.StatusCode.NO_CHANGES

        old_updated = SanitazerService.safe_make_aware(sync_logs_obj.old_value_updated)
        new_updated = SanitazerService.safe_make_aware(sync_logs_obj.new_value_updated)
        if old_updated > new_updated:
            return sync_logs_obj.StatusCode.IGNORE

        return sync_logs_obj.status_code

    @staticmethod
    def repeat_update_remote_contacts(sync_parameters_logs_id: int):
        sync_parameters_logs_obj = Sync_Parameters_Logs.objects.get(id=sync_parameters_logs_id)

        sync_parameters_logs_obj.status_code = sync_parameters_logs_obj.StatusCode.IN_PROGRESS
        correct_status = SyncInstantService.get_correct_status(sync_parameters_logs_obj)
        sync_parameters_logs_obj.status_code = correct_status
        sync_parameters_logs_obj.save()

        SyncInstantService.update_remote_contacts(
            [sync_parameters_logs_obj],
            employee_obj=sync_parameters_logs_obj.employee,
            contact_privser_obj=sync_parameters_logs_obj.contact_privser
        )
