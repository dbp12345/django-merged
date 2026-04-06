# import time
#
# from django.core.exceptions import ObjectDoesNotExist
#
# from company.models import Employees
# from core.services.SanitazerService import SanitazerService
# from company.models.EmployeesParameters import Employees_Parameters
# from privser.models.ContactsParameters import Contacts_Parameters as Contacts_Parameters_Privser
# from privser.models.CustomFields import Custom_Fields
# from privser.services.PrivserAPI2Service import PrivserAPI2Service
# from synchronization.models.Sync import Sync
# from synchronization.models.SyncParameters import Sync_Parameters
# from privser.models import Contacts as ContactsPrivser
#
#
# class SyncService:
#     # @staticmethod
#     # def handle_changed_properties_task(
#     #         employee_id: str = None,
#     #         contact_privser_id: str = None,
#     #         changed_properties_privser: dict = None,
#     #         changed_properties_exchange: dict = None
#     # ):
#     #     from core.tasks.sync_tasks import add_sync_to_db_task
#     #     add_sync_to_db_task.apply_async(
#     #         kwargs={
#     #             "employee_id": employee_id,
#     #             "contact_privser_id": contact_privser_id,
#     #             "changed_properties_privser": changed_properties_privser,
#     #             "changed_properties_exchange": changed_properties_exchange
#     #         }
#     #     )
#
#     @staticmethod
#     # @transaction.atomic
#     def handle_changed_properties_exchange(
#             employee_obj,
#             changed_properties_exchange: dict = None
#     ):
#         """
#         :param employee_obj:
#         :param changed_properties_exchange: [key: exchange.Contacts_Prop, value]
#         :return:
#         """
#         if changed_properties_exchange is None:
#             changed_properties_exchange = {}
#         email = employee_obj.email
#
#         try:
#             contact_privser_obj = ContactsPrivser.objects.get(email=email)
#         except ObjectDoesNotExist:
#             contact_privser_obj = None
#
#         sync_obj, created = Sync.objects.get_or_create(
#             email=email,
#             defaults={
#                 "status_code": Sync.StatusCode.NEW
#             }
#         )
#
#         if employee_obj and sync_obj.employee is None:
#             sync_obj.employee = employee_obj
#         if contact_privser_obj and sync_obj.contact_privser is None:
#             sync_obj.contact_privser = contact_privser_obj
#         sync_obj.save()
#
#         if changed_properties_exchange:
#             for key, value in changed_properties_exchange.items():
#                 no_sync = False
#                 custom_fields_obj = Custom_Fields.objects.filter(exchange_property=key)
#
#                 error = []
#                 if not custom_fields_obj.exists():
#                     sync_parameters_obj, created = Sync_Parameters.objects.update_or_create(
#                         sync=sync_obj,
#                         exchange_property_not_found=key.property_name,
#                         body={"error": "Custom fields not matched/linked"},
#                         defaults={
#                             "exchange_value": value,
#                         }
#                     )
#                 elif custom_fields_obj.count() > 1:
#                     sync_parameters_obj, created = Sync_Parameters.objects.update_or_create(
#                         sync=sync_obj,
#                         exchange_property_not_found=key.property_name,
#                         body={"error": "Custom fields found multiple matches/links"},
#                         defaults={
#                             "exchange_value": value,
#                         }
#                     )
#                 else:
#                     custom_fields_obj_first = custom_fields_obj.first()
#                     no_sync = custom_fields_obj_first.no_sync
#                     # Будем брать пока значения из приходящего value, потому что сложно работать с параметрами, которые уже переделали на обьекты
#                     # и да, мы потеряем при этом exchange_datetime_from_db
#                     try:
#                         employees_parameters_obj = Employees_Parameters.objects.get(
#                             employee=employee_obj,
#                             contacts_prop=custom_fields_obj_first.exchange_property,
#                         )
#                         exchange_value_from_db = employees_parameters_obj.value
#                         exchange_datetime_from_db = employees_parameters_obj.updated_at
#                         # print("employees_parameters_obj.id", employees_parameters_obj.id)
#                         # print("employees_parameters_obj.updated_at", employees_parameters_obj.updated_at)
#                     except Exception as e:
#                         # error.append(str(e)) #["Contacts_Parameters matching query does not exist."]
#                         exchange_value_from_db = None
#                         exchange_datetime_from_db = None
#                     # exchange_value_from_db = value
#                     # exchange_datetime_from_db = datetime.now().astimezone()
#
#                     try:
#                         if contact_privser_obj:
#                             contacts_parameters_privser_obj = Contacts_Parameters_Privser.objects.get(
#                                 contacts=contact_privser_obj,
#                                 name__in=[custom_fields_obj_first.privser_name, custom_fields_obj_first.privser_id],
#                             )
#                             # privser_value_from_db = SanitazerService.normalize_to_str_by_property_type_for_privser(
#                             #     value=contacts_parameters_privser_obj.value,
#                             #     property_type=custom_fields_obj_first.privser_dataType,
#                             #     output_format="%Y-%m-%d"
#                             # )
#                             privser_value_from_db = contacts_parameters_privser_obj.value
#                             privser_datetime_from_db = contacts_parameters_privser_obj.updated_at
#
#                             privser_value_from_db = SanitazerService.convert_date_format_str(
#                                 value=privser_value_from_db,
#                                 from_format="%Y-%m-%d",
#                                 output_format=custom_fields_obj_first.exchange_property.datetime_format
#                             )
#                         else:
#                             privser_value_from_db = None
#                             privser_datetime_from_db = None
#                     except Exception as e:
#                         # error.append(str(e))
#                         privser_value_from_db = None
#                         privser_datetime_from_db = None
#
#                     sync_parameters_obj, created = Sync_Parameters.objects.update_or_create(
#                         sync=sync_obj,
#                         privser_custom_fields=custom_fields_obj_first,
#                         defaults={
#                             "privser_value": privser_value_from_db,
#                             "privser_datetime": privser_datetime_from_db,
#                             "exchange_value": exchange_value_from_db,
#                             "exchange_datetime": exchange_datetime_from_db,
#                             "body": error
#                         }
#                     )
#
#                 # if not created:
#                 #     sync_parameters_obj.exchange_value = exchange_value_from_db
#                 #     sync_parameters_obj.exchange_datetime = exchange_datetime_from_db
#                 #     sync_parameters_obj.privser_value = privser_value_from_db
#                 #     sync_parameters_obj.privser_datetime = privser_datetime_from_db
#                 #     sync_parameters_obj.body = error
#
#                 if no_sync:
#                     sync_parameters_obj.removed = True
#                 else:
#                     if key.property_name == "MobilePhone":
#                         sync_parameters_obj.removed = SanitazerService.contains_phone(sync_parameters_obj.exchange_value, sync_parameters_obj.privser_value)
#                     else:
#                         sync_parameters_obj.removed = (
#                                 (str(sync_parameters_obj.exchange_value) or "").replace("\r", "").replace("\n", "").lower() ==
#                                 (str(sync_parameters_obj.privser_value) or "").replace("\r", "").replace("\n", "").lower()
#                         )
#                 sync_parameters_obj.save()
#
#         status_code = SyncService.get_correct_status(sync_obj)
#         sync_obj.status_code = status_code
#         sync_obj.save()
#
#
#     @staticmethod
#     # @transaction.atomic
#     def handle_changed_properties_privser(
#             contact_privser_id: int = None,
#             changed_properties_privser: dict = None,
#     ):
#         if changed_properties_privser is None:
#             changed_properties_privser = {}
#         email = None
#         email_empty = False
#         employee_obj = None
#         contact_privser_obj = None
#
#         if contact_privser_id:
#             contact_privser_obj = ContactsPrivser.objects.get(id=contact_privser_id)
#             email = contact_privser_obj.email
#             if not email:
#                 email = f"Privser: {contact_privser_obj.id}, (email_empty)"
#                 email_empty = True
#             else:
#                 employee_obj = Employees.objects.filter(email=email).first()
#
#         if not email:
#             raise RuntimeError(f"Сan't find email")
#
#         changed_properties_privser.pop('lastActivity', None)
#         changed_properties_privser.pop('date_updated', None)
#         changed_properties_privser.pop('contactName', None)
#
#         sync_obj, created = Sync.objects.get_or_create(
#             email=email,
#             defaults={
#                 "status_code": Sync.StatusCode.NEW
#             }
#         )
#
#         if employee_obj and sync_obj.employee is None:
#             sync_obj.employee = employee_obj
#
#         if contact_privser_obj and sync_obj.contact_privser is None:
#             sync_obj.contact_privser = contact_privser_obj
#
#         sync_obj.save()
#
#         if changed_properties_privser:
#             from django.db.models import Q
#             # changed_properties_privser = PrivserService.update_keys_by_mapping(changed_properties_privser)
#             for key, value in changed_properties_privser.items():
#                 no_sync = False
#                 custom_fields_obj = Custom_Fields.objects.filter(
#                     Q(privser_id=key) | Q(privser_name=key)
#                 )
#
#                 error = []
#                 if not custom_fields_obj.exists():
#                     sync_parameters_obj, created = Sync_Parameters.objects.update_or_create(
#                         sync=sync_obj,
#                         privser_property_not_found=key,
#                         body={"error": "Custom fields not matched/linked"},
#                         defaults={
#                             "privser_value": value,
#                         }
#                     )
#                 elif custom_fields_obj.count() > 1:
#                     sync_parameters_obj, created = Sync_Parameters.objects.update_or_create(
#                         sync=sync_obj,
#                         privser_property_not_found=key,
#                         body={"error": "Custom fields found multiple matches/links"},
#                         defaults={
#                             "privser_value": value,
#                         }
#                     )
#                 else:
#                     custom_fields_obj_first = custom_fields_obj.first()
#                     no_sync = custom_fields_obj_first.no_sync
#                     try:
#                         if not email_empty:
#                             employees_parameters_obj = Employees_Parameters.objects.get(
#                                 employee=employee_obj,
#                                 contacts_prop=custom_fields_obj_first.exchange_property,
#                             )
#                             exchange_value_from_db = employees_parameters_obj.value
#                             exchange_datetime_from_db = employees_parameters_obj.updated_at
#                         else:
#                             exchange_value_from_db = None
#                             exchange_datetime_from_db = None
#                     except Exception as e:
#                         # error.append(str(e))
#                         exchange_value_from_db = None
#                         exchange_datetime_from_db = None
#
#                     try:
#                         contacts_parameters_privser_obj = Contacts_Parameters_Privser.objects.get(
#                             contacts=contact_privser_obj,
#                             name__in=[custom_fields_obj_first.privser_name, custom_fields_obj_first.privser_id],
#                         )
#                         # privser_value_from_db = SanitazerService.normalize_to_str_by_property_type_for_privser(
#                         #     value=contacts_parameters_privser_obj.value,
#                         #     property_type=custom_fields_obj_first.privser_dataType,
#                         #     output_format="%Y-%m-%d"
#                         # )
#                         privser_value_from_db = contacts_parameters_privser_obj.value
#                         privser_value_from_db = SanitazerService.convert_date_format_str(
#                             value=privser_value_from_db,
#                             from_format="%Y-%m-%d",
#                             output_format=custom_fields_obj_first.exchange_property.datetime_format
#                         )
#                         privser_datetime_from_db = contacts_parameters_privser_obj.updated_at
#                     except Exception as e:
#                         # error.append(str(e)) #["Contacts_Parameters matching query does not exist."]
#                         privser_value_from_db = None
#                         privser_datetime_from_db = None
#
#                     sync_parameters_obj, created = Sync_Parameters.objects.update_or_create(
#                         sync=sync_obj,
#                         privser_custom_fields=custom_fields_obj_first,
#                         defaults={
#                             "privser_value": privser_value_from_db,
#                             "privser_datetime": privser_datetime_from_db,
#                             "exchange_value": exchange_value_from_db,
#                             "exchange_datetime": exchange_datetime_from_db,
#                             "body": error
#                         }
#                     )
#
#                 # if not created:
#                 #     sync_parameters_obj.exchange_value = exchange_value_from_db
#                 #     sync_parameters_obj.exchange_datetime = exchange_datetime_from_db
#                 #     sync_parameters_obj.privser_value = privser_value_from_db
#                 #     sync_parameters_obj.privser_datetime = privser_datetime_from_db
#                 #     sync_parameters_obj.body = error
#
#                 if no_sync:
#                     sync_parameters_obj.removed = True
#                 else:
#                     # Privser outputs names with lowercase capitalization (an error on its part)
#                     # if key in ["firstName", "lastName"]:
#                     #     sync_parameters_obj.removed = (
#                     #             (sync_parameters_obj.exchange_value or "").replace("\r", "").replace("\n", "").lower() ==
#                     #             (sync_parameters_obj.privser_value or "").replace("\r", "").replace("\n", "").lower()
#                     #     )
#                     # else:
#                     #     sync_parameters_obj.removed = sync_parameters_obj.exchange_value == sync_parameters_obj.privser_value
#                     if key == "phone":
#                         sync_parameters_obj.removed = SanitazerService.contains_phone(sync_parameters_obj.exchange_value, sync_parameters_obj.privser_value)
#                     else:
#                         sync_parameters_obj.removed = (
#                                 (str(sync_parameters_obj.exchange_value) or "").replace("\r", "").replace("\n", "").lower() ==
#                                 (str(sync_parameters_obj.privser_value) or "").replace("\r", "").replace("\n", "").lower()
#                         )
#                 sync_parameters_obj.save()
#
#         status_code = SyncService.get_correct_status(sync_obj)
#         sync_obj.status_code = status_code
#         sync_obj.save()
#
#     @staticmethod
#     def get_correct_status(sync_obj: Sync):
#         if not isinstance(sync_obj, Sync):
#             raise TypeError(f"Invalid object type: {type(sync_obj).__name__}")
#
#         # from exchange.services.ExchangeService import ExchangeService
#         # _, status = ExchangeService.find_user_by_email(email=sync_obj.employee.email)
#
#         if not sync_obj.employee or not sync_obj.contact_privser:
#             return Sync.StatusCode.USER_NOT_FOUND
#
#         if sync_obj.sync_parameters.filter(removed=False).exists():
#             return Sync.StatusCode.IN_PROGRESS
#         else:
#             return Sync.StatusCode.NO_CHANGES
#
#     @staticmethod
#     def update_remote_contacts(sync_obj: Sync):
#         if not isinstance(sync_obj, Sync):
#             raise TypeError(f"Invalid object type: {type(sync_obj).__name__}")
#
#         sync_main_fields_privser_dict = {}
#         sync_custom_fields_privser_dict = []
#         sync_parameters_exchange_dict = {}
#         sync_main_fields_privser_id_sync_dict = {}
#         sync_custom_fields_privser_id_sync_dict = {}
#         for sync_parameters_i in sync_obj.get_active_parameters():
#             # Skip if both conditions are true
#             if sync_parameters_i.privser_apply and sync_parameters_i.exchange_apply:
#                 continue
#
#             if sync_parameters_i.override_value:
#                 sync_parameters_i.privser_apply = True
#                 sync_parameters_i.exchange_apply = True
#                 sync_parameters_i.exchange_value = sync_parameters_i.override_value
#                 sync_parameters_i.privser_value = sync_parameters_i.override_value
#                 sync_parameters_i.override_value = None
#                 sync_parameters_i.save()
#
#             # Skip if both conditions are false
#             if not sync_parameters_i.privser_apply and not sync_parameters_i.exchange_apply:
#                 continue
#
#             if sync_parameters_i.exchange_apply and sync_parameters_i.privser_custom_fields:
#                 exchange_value = SanitazerService.convert_date_format_str(
#                     value=sync_parameters_i.exchange_value,
#                     from_format=sync_parameters_i.privser_custom_fields.exchange_property.datetime_format,
#                     output_format="%Y-%m-%d"
#                 )
#                 if sync_parameters_i.privser_custom_fields.main_field:
#                     sync_main_fields_privser_dict[sync_parameters_i.privser_custom_fields.privser_name] = exchange_value
#                     sync_main_fields_privser_id_sync_dict[sync_parameters_i.privser_custom_fields.privser_name] = sync_parameters_i.id
#                 else:
#                     sync_custom_fields_privser_dict.append({
#                         "id": sync_parameters_i.privser_custom_fields.privser_id,
#                         "key": sync_parameters_i.privser_custom_fields.privser_name,
#                         "field_value": exchange_value
#                     })
#                     sync_custom_fields_privser_id_sync_dict[sync_parameters_i.privser_custom_fields.privser_id] = sync_parameters_i.id
#
#             if sync_parameters_i.privser_apply and sync_parameters_i.privser_custom_fields:
#                 if sync_parameters_i.privser_custom_fields.exchange_property is None:
#                     raise Exception(f"No link to Privser field name: '{sync_parameters_i.privser_custom_fields.privser_name}'")
#                 sync_parameters_exchange_dict[sync_parameters_i.privser_custom_fields.exchange_property.property_name] = sync_parameters_i.privser_value
#                 continue
#
#         # UPDATE IN PRIVSER:
#         if (sync_main_fields_privser_dict or sync_custom_fields_privser_dict) and sync_obj.contact_privser:
#             privser_api2_service = PrivserAPI2Service()
#             # contact_id = privser_api2_service.get_contacts_by_email(sync_obj.email).get("id")
#
#             # sync_main_fields_privser_dict = {'dateOfBirth': '2011-01-11 11:00:00', 'firstName': 'Test-8fn'}
#             # sync_custom_fields_privser_dict = {'04rXHtJ3rctIgAXu39aM': 'Test-114', 'PQQjv7xlRat4kyGjGZlc': 'Test-8444', '7uSOnJcfst4XQski7gGU': '1'}
#             # {
#             #   "id": "6dvNaf7VhkQ9snc5vnjJ",
#             #   "key": "my_custom_field",
#             #   "field_value": "9039160788"
#             # }
#
#             notes = sync_main_fields_privser_dict.pop("Notes", None)
#             if notes:
#                 response = privser_api2_service.create_note(
#                     contact_id=sync_obj.contact_privser.contact_id,
#                     body=notes
#                 )
#                 note_id_new = response.get("note").get("id")
#
#                 response = privser_api2_service.get_all_notes(sync_obj.contact_privser.contact_id)
#                 from privser.services.PrivserService import PrivserService
#                 privser_service = PrivserService()
#                 ids = privser_service.all_notes_ids_from_res(response)
#                 ids.remove(note_id_new)
#                 for note_id in ids:
#                     privser_api2_service.delete_note(contact_id=sync_obj.contact_privser.contact_id, note_id=note_id)
#
#             response_privser = privser_api2_service.update_contacts_fields(
#                 sync_obj.contact_privser.contact_id,
#                 main_fields=sync_main_fields_privser_dict,
#                 custom_fields_list=sync_custom_fields_privser_dict
#             )
#
#             # response_main_fields = response_privser.get("contact")
#             # for key, value in sync_main_fields_privser_dict.items():
#             #     result = response_main_fields.get(key)
#             #     if str(result) == str(value):
#             #         # sync_parameters_object = Sync_Parameters.objects.get(sync=sync_obj, privser_custom_fields__privser_name=key)
#             #         sync_parameters_object = Sync_Parameters.objects.get(id=sync_main_fields_privser_id_sync_dict[key])
#             #         sync_parameters_object.removed = True
#             #         sync_parameters_object.body = {"removed": "from_privser"}
#             #         sync_parameters_object.save()
#
#             # print("REMOVE-main: ", key)
#             # sync_parameters_object = Sync_Parameters.objects.get(id=sync_main_fields_privser_id_sync_dict[key])
#             # sync_parameters_object.removed = True
#             # sync_parameters_object.save(update_fields=["removed"])
#
#             # response_custom_field = response_privser.get("contact").get("customFields")
#             # for sync_custom_fields_privser in sync_custom_fields_privser_dict:
#             #     result = next((item.get("value") for item in response_custom_field if item.get("id") == key), None)
#             #     if str(result) == str(sync_custom_fields_privser.get("value")):
#             #         # sync_parameters_object = Sync_Parameters.objects.get(sync=sync_obj, privser_custom_fields__privser_id=key)
#             #         sync_parameters_object = Sync_Parameters.objects.get(id=sync_custom_fields_privser_id_sync_dict[sync_custom_fields_privser.get("id")])
#             #         sync_parameters_object.removed = True
#             #         sync_parameters_object.body = {"removed": "from_privser"}
#             #         sync_parameters_object.save()
#
#             # print("REMOVE-custom: ", key)
#             # sync_parameters_object = Sync_Parameters.objects.get(id=sync_custom_fields_privser_id_sync_dict[key])
#             # sync_parameters_object.removed = True
#             # sync_parameters_object.save(update_fields=["removed"])
#
#             # Privser отдает ответ, но сам долго думает и обновляет данные. Если сразу после сохранение в него запросить их обратно для проверки, то они будут старые
#             # сделаю этот таймаут для того, чтобы не выполнять проверку выше из отданных наспех данных из Privser
#             time.sleep(2)
#             from privser.services.PrivserUpdatesService import PrivserUpdatesService
#             PrivserUpdatesService.update_all_fields_from_contact_id(sync_obj.contact_privser.contact_id, ignore_diff_properties=False)
#
#         # print("sync_main_fields_privser_dict:", sync_main_fields_privser_dict)
#         # print("sync_custom_fields_privser_dict:", sync_custom_fields_privser_dict)
#         # print("sync_parameters_exchange_dict:", sync_parameters_exchange_dict)
#
#         # UPDATE IN EXCHANGE:
#         if sync_parameters_exchange_dict and sync_obj.employee:
#             from exchange.services.ExchangeApiService import ExchangeApiService
#             from exchange.services.ExchangeUpdatesService import ExchangeUpdatesService
#             ExchangeApiService.update_exc_contact_by_email_with_data(email=sync_obj.employee.email, data=sync_parameters_exchange_dict)
#             ExchangeUpdatesService.do_update_from_exchange_by_email(email=sync_obj.employee.email, ignore_diff_properties=False)
#
#     @staticmethod
#     def update_all_sync_by_email(email):
#         contacts_obj = ContactsPrivser.objects.filter(email=email).first()
#         changed_properties_new = {}
#         if contacts_obj:
#             for param_i in contacts_obj.parameters.all():
#                 # print(prop_i.contacts_parameters.visibility)
#                 # print(prop_i.name)
#                 # print(prop_i.value)
#                 changed_properties_new[param_i.name] = param_i.value
#             SyncService.handle_changed_properties_privser(contact_privser_id=contacts_obj.id, changed_properties_privser=changed_properties_new)
#
#         contacts_obj = Employees.objects.filter(email=email).first()
#         changed_properties_new = {}
#         if contacts_obj:
#             for employees_parameters_i in contacts_obj.employees_parameters_entries.all():
#                 # Исправление для согласования с новой структурой модели
#                 # print(prop_i.contacts_parameters.property_name)
#                 # print(prop_i.value)
#                 changed_properties_new[employees_parameters_i.contacts_prop] = employees_parameters_i.value
#             SyncService.handle_changed_properties_exchange(employee_obj=contacts_obj, changed_properties_exchange=changed_properties_new)
