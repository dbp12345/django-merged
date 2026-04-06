import traceback

from celery import group
from datetime import datetime, timedelta

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.timezone import localtime

from company.services.EmployeesService import EmployeesService
from core.models.EmployeeLastUpdates import ApiType
from core.services.SanitazerService import SanitazerService
from exchange.models import Contacts_Prop
from exchange.services.ExchangeService import ExchangeService
from core.tasks.exchange_tasks import update_from_exchange_task
import logging


# Памятка, какбы пропал смысл разбивать по интервалам дат, поскольку мы обновили все контакты новой формой и
#  теперь у всех контактов last_modified_time примерно в одно время = "2025-01-22 23:59:02.000000"
class ExchangeUpdatesService(ExchangeService):
    @staticmethod
    def do_update_from_exchange_handle(ignore_diff_properties=False, after_date_str: str = None, update_all=False):
        print("start")
        if after_date_str:
            print("___")
            print("Do: after_date_str")
            print("___")
            update_from_exchange_task.apply_async(
                kwargs={
                    "datetime_after_str": after_date_str,
                    "ignore_diff_properties": ignore_diff_properties
                }
            )

        if update_all:
            print("___")
            print("Do: update_all")
            print("___")
            total_contacts = ExchangeService.get_total_contacts()
            batch_size = 100
            total_pages = (total_contacts + batch_size - 1) // batch_size

            print("Total contacts: ", total_contacts)
            print("Total pages: ", total_pages)
            print("___")

            # асинхронно запускать задачи по мере итерации
            # for page_number in range(total_pages):
            #     offset = page_number * batch_size
            #     update_from_exchange_task.apply_async(
            #         kwargs={
            #             "offset": offset,
            #             "batch_size": batch_size,
            #             "ignore_diff_properties": ignore_diff_properties
            #         }
            #     )
            # Это полезно, когда нужно запустить множество задач параллельно и потенциально обработать результаты в целом
            # Отработало хорошо. С Retry

            if settings.DEBUG:
                folder = ExchangeService.get_exchange_folder()
                for page_number in range(total_pages):
                    print("page_number: ", page_number)
                    contacts = ExchangeUpdatesService.get_last_modified_contacts_by_batch(
                        offset=page_number * batch_size,
                        batch_size=batch_size,
                        folder=folder
                    )
                    ExchangeUpdatesService.do_update_from_exchange(
                        exc_contacts=contacts,
                        ignore_diff_properties=ignore_diff_properties,
                        folder=folder
                    )
            else:
                group_tasks = group(
                    update_from_exchange_task.si(
                        **{
                            "offset": page_number * batch_size,
                            "batch_size": batch_size,
                            "ignore_diff_properties": ignore_diff_properties
                        }
                    )
                    for page_number in range(total_pages)
                )
                group_tasks.apply_async()
                # logger = logging.getLogger("my_info")
                # folder = ExchangeService.get_exchange_folder()
                # for page_number in range(total_pages):
                #     if page_number >14:
                #         print("page_number:", page_number)
                #         contacts = ExchangeUpdatesService.get_last_modified_contacts_by_batch(
                #             offset=page_number * batch_size,
                #             batch_size=batch_size,
                #             folder=folder
                #         )
                #         ExchangeUpdatesService.do_update_from_exchange(
                #             exc_contacts=contacts,
                #             ignore_diff_properties=ignore_diff_properties,
                #             folder=folder
                #         )
                #         time.sleep(1)
                #         print("================ do_update_from_exchange_handle ================")
                #         print("Done page№:", page_number)
                #         logger.info(
                #             "\n================ do_update_from_exchange_handle ================\n"
                #             f"Done page№: {page_number}\n"
                #         )
                        


                # for i, page_number in enumerate(range(total_pages)):
                #     update_from_exchange_task.apply_async(
                #         kwargs={
                #             "offset": page_number * batch_size,
                #             "batch_size": batch_size,
                #             "ignore_diff_properties": ignore_diff_properties
                #         },
                #         countdown=i * 5  # 5 секунд между задачами
                #     )
                    
                    
            # # не опробовал.Это для очередного выполнение задач
            # tasks = (
            #     update_from_exchange_task.s(offset=page_number * batch_size, batch_size=batch_size, ignore_diff_properties=ignore_diff_properties)
            #     for page_number in range(total_pages)
            # )
            #
            # # Создание цепочки задач
            # chained_tasks = chain(*tasks).apply_async()

            # очередной подход от gpt
            # tasks = [
            #     update_from_exchange_task.si(
            #         offset=page_number * batch_size,
            #         batch_size=batch_size,
            #         ignore_diff_properties=ignore_diff_properties
            #     )
            #     for page_number in range(total_pages)
            # ]
            # group_tasks = group(tasks)
            # for i, task in enumerate(group_tasks.tasks):
            #     task.apply_async(countdown=i * 2)

        # if monthly:
        #     monthly_datetime_ranges = ExchangeUpdatesService.generate_monthly_datetime_ranges(start_date_str=after_date_str)
        #     group_tasks = group(
        #         update_from_exchange_task.si(
        #             **{
        #                 "datetime_after_str": i.get("from"),
        #                 "datetime_before_str": i.get("to"),
        #                 "ignore_diff_properties": ignore_diff_properties
        #             }
        #         )
        #         for i in monthly_datetime_ranges
        #     )
        #     group_tasks.apply_async()

    @staticmethod
    def do_update_unprocessed_from_exchange(ignore_diff_properties: bool = False) -> list[str]:
        employee_lu_obj = EmployeesService.get_employee_last_updates(type_api=ApiType.EXCHANGE)
        last_modified_time = localtime(employee_lu_obj.date_updated)
        # contact_exc_id = employee_lu_obj.contact_id

        last_modified_time_ews = SanitazerService.datetime_to_ewsdatetime(last_modified_time)
        folder = ExchangeService.get_exchange_folder()
        exc_contacts = folder.filter(last_modified_time__gte=last_modified_time_ews).order_by("last_modified_time")
        # filtered_contacts = [c for c in exc_contacts if c.id != contact_exc_id]
        return ExchangeUpdatesService.do_update_from_exchange(exc_contacts=exc_contacts, ignore_diff_properties=ignore_diff_properties)

    @staticmethod
    def do_update_from_exchange_by_email(email: str, ignore_diff_properties: bool = False, folder = None):
        contacts_prop_list = ExchangeService.contact_register_and_get_all_properties()
        contact_exc = ExchangeService.find_user_by_email(contact_exc_email=email, folder = folder)
        res_email = None
        try:
            res_email = ExchangeUpdatesService.save_last_modified_contact_and_changed_properties(
                contact=contact_exc,
                ignore_diff_properties=ignore_diff_properties
            )
        except Exception:
            logger = logging.getLogger("my_log")
            logger.error(
                "\n================ do_update_from_exchange_by_email ================\n"
                f"Lost contact exc: {contact_exc}\n{traceback.format_exc()}\n"
            )
            raise
        finally:
            ExchangeService.contact_deregister_properties([c.property_name for c in contacts_prop_list])

        return res_email

    @staticmethod
    def do_update_from_exchange_sub(
            datetime_after=None,
            datetime_after_str=None,
            datetime_before_str=None,
            offset=None,
            batch_size=None,
            ignore_diff_properties: bool = False
    ) -> list[str]:
        last_modified_contacts = ExchangeUpdatesService.get_last_modified_contacts(
            datetime_after=datetime_after,
            datetime_after_str=datetime_after_str,
            datetime_before_str=datetime_before_str,
            offset=offset,
            batch_size=batch_size,
        )
        return ExchangeUpdatesService.do_update_from_exchange(exc_contacts=last_modified_contacts, ignore_diff_properties=ignore_diff_properties)

    @staticmethod
    def do_update_from_exchange(exc_contacts, ignore_diff_properties: bool = False, folder=None) -> list[str]:
        list_of_changed_emails = []
        # if folder is None:
        #     folder = ExchangeService.get_exchange_folder()
        if exc_contacts:
            for contact in exc_contacts:
                contacts_prop_list = []
                try:
                    # Это!! НАДО! Но оно не сработало! ХЗ почему...
                    # contact_email = next((email.email for email in contact.email_addresses if email.label == 'EmailAddress1'), None)
                    # if not contact_email and contact.email_addresses:
                    #     contact_email = contact.email_addresses[0].email
                    # contact = ExchangeService.find_user_by_email(contact_exc_email=contact_email, folder=folder)
                    contacts_prop_list = ExchangeService.contact_register_and_get_all_properties()
                    email = ExchangeUpdatesService.save_last_modified_contact_and_changed_properties(contact=contact, ignore_diff_properties=ignore_diff_properties)
                    list_of_changed_emails.append(email)
                except:
                    error_text = traceback.format_exc()
                    logger = logging.getLogger("my_log")
                    logger.error(
                        "\n================ do_update_from_exchange ================\n"
                        f"Lost contact exc: {contact.id}__{contact.file_as}\n{error_text}\n"
                    )
                finally:
                    # ExchangeService.contact_deregister_properties(property_name_arr)
                    for contacts_prop in contacts_prop_list:
                        ExchangeService.contact_deregister_properties([contacts_prop.property_name])
            ExchangeUpdatesService.set_last_modified_date_from_contacts(exc_contacts)
        return list_of_changed_emails

    @staticmethod
    def set_last_modified_date_from_contacts(contacts):
        # if not contacts.exists():
        #     return
        # latest_contact = max(contacts, key=lambda x: x.last_modified_time)

        try:
            latest_contact = max(contacts, key=lambda x: x.last_modified_time, default=None)
            if latest_contact:
                last_modified_time_datetime = SanitazerService.format_ewsdatetime_to_datetime(latest_contact.last_modified_time)

                last_modified_time_datetime_plus_one_second = last_modified_time_datetime + timedelta(seconds=1)

                # Берём email из contact
                email = None
                if latest_contact.email_addresses:
                    email_obj = next((e for e in latest_contact.email_addresses if e.label == "EmailAddress1"), None)
                    if email_obj:
                        email = email_obj.email
                    elif latest_contact.email_addresses[0].email:
                        email = latest_contact.email_addresses[0].email

                if email:
                    EmployeesService.save_or_update_employee_last_updates(
                        contact_id=email,
                        type_api=ApiType.EXCHANGE,
                        date_updated=last_modified_time_datetime_plus_one_second
                    )
        except ValueError:
            return


    # @staticmethod
    # def get_last_modified_time_from_db():
    #     return Employees.objects.latest("last_modified_time").last_modified_time

    @staticmethod
    def get_last_modified_contacts(
            datetime_after=None,
            datetime_after_str=None,
            datetime_before_str=None,
            offset=None,
            batch_size=None,
    ):
        if datetime_after and datetime_before_str:
            return ExchangeUpdatesService.get_last_modified_contacts_by_time(
                datetime_after=datetime_after,
                datetime_before_str=datetime_before_str
            )
        elif offset is not None and batch_size is not None:
            return ExchangeUpdatesService.get_last_modified_contacts_by_batch(
                offset=offset,
                batch_size=batch_size
            )
        elif datetime_after:
            return ExchangeUpdatesService.get_last_modified_contacts_by_time(
                datetime_after=datetime_after
            )
        elif datetime_after_str:
            return ExchangeUpdatesService.get_last_modified_contacts_by_time(
                datetime_after_str=datetime_after_str
            )

        return None

    @staticmethod
    def get_last_modified_contacts_by_time(
            datetime_after = None,
            datetime_after_str = None,
            datetime_before_str=None
    ):
        # WARNING We do this because the Exchange gives us the object without microseconds. And when we ask him to give us everything that is older, he constantly gives us this object.
        # datetime_after = datetime.strptime(datetime_after_str, "%Y-%m-%d %H:%M:%S")
        # datetime_after_plus_one_second = datetime_after + timedelta(seconds=1)

        if datetime_after_str:
            datetime_after = datetime.strptime(datetime_after_str, "%Y-%m-%d %H:%M:%S")

        datetime_after_ews = SanitazerService.datetime_to_ewsdatetime(datetime_after)
        folder = ExchangeService.get_exchange_folder()

        # We will always update here, and we will transfer “Exchange Sync” to sending changes via API
        # contacts = folder.filter(last_modified_time__gt = datetime_after_plus_one_second).order_by("last_modified_time").exclude(last_modified_name="Exchange Sync")

        # if datetime_before_str:
        #     datetime_before = SanitazerService.datetime_str_to_ewsdatetime(datetime_before_str)
        #     contacts = folder.filter(last_modified_time__gt=datetime_after_plus_one_second, last_modified_time__lt=datetime_before).order_by(
        #         "last_modified_time")
        # else:
        #     contacts = folder.filter(last_modified_time__gt=datetime_after_plus_one_second).order_by("last_modified_time")

        contacts = folder.filter(last_modified_time__gte=datetime_after_ews).order_by("last_modified_time")

        if contacts.exists():
            return contacts
        else:
            return None

    @staticmethod
    def get_last_modified_contacts_by_batch(offset, batch_size, folder=None):
        # if folder is None:
        #     folder = ExchangeService.get_exchange_folder()
        # test_emails = ["2dmytro.svietnoi@gmail.com", "2test10@automation.com", "2test11@automation.com"]  # Список email-адресов, которые тебе нужны
        # contacts = ExchangeService.get_exchange_folder().filter(email_addresses__in=test_emails).order_by("last_modified_time")[offset:offset + batch_size]
        folder = ExchangeService.get_exchange_folder()
        contacts = folder.all().order_by("last_modified_time")[offset:offset + batch_size]
        if contacts:
            return contacts
        else:
            return []

    @staticmethod
    def save_last_modified_contact_and_changed_properties(contact, ignore_diff_properties: bool = False) -> str:
        if not contact:
            return "No contact provided"

        last_modified_time_datetime = SanitazerService.format_ewsdatetime_to_datetime(contact.last_modified_time)
        datetime_created_datetime = SanitazerService.format_ewsdatetime_to_datetime(contact.datetime_created)

        try:
            contact_email = next((email.email for email in contact.email_addresses if email.label == 'EmailAddress1'), None)
            if not contact_email and contact.email_addresses:
                contact_email = contact.email_addresses[0].email
        except Exception:
            contact_email = None

            # str(contact.email_addresses)
            # print("Cant get Email[0].email")
            # print(contact.email_addresses)
            # return f"ERROR: Exchange c.id - {contact.id}, display_name = {contact.display_name}"
            # display_name иногда с ошибкой: AttributeError: 'PostItem' object has no attribute 'display_name'. Did you mean: 'display_cc'?
            # return f"ERROR: Exchange c.id - {contact.id}"

        if not contact_email:
            # TO-DO remove this
            return f"No email for contact {contact.file_as}"

        print("contact_email", contact_email)

        employees_service = EmployeesService()
        employee_obj, _ = employees_service.update_or_create_contact(
            contact_id=contact.id,
            email=contact_email,
            last_modified_name=contact.last_modified_name,
            last_modified_time=last_modified_time_datetime,
            datetime_created=datetime_created_datetime,
        )

        contacts_prop_db = Contacts_Prop.objects.filter()
        for c_prop_i in contacts_prop_db:
            property_name_str = c_prop_i.property_name
            if property_name_str == "MobilePhone":
                new_value = getattr(contact, "phone_numbers", None) or []
                if new_value:
                    new_value = next(
                        (phone.phone_number for phone in new_value if phone.label == 'MobilePhone'),
                        None
                    )
                else:
                    new_value = None

            elif property_name_str == "Email":
                new_value = getattr(contact, "email_addresses", None) or []
                if new_value:
                    new_value = next(
                        (email.email for email in new_value if email.label == 'EmailAddress1'),
                        None
                    )
                else:
                    new_value = None

            elif property_name_str == "file_as":
                new_value = contact.file_as

            else:
                new_value = getattr(contact, property_name_str, None)

            new_value = SanitazerService.normalize_to_str_by_property_type_from_exchange(
                value=new_value,
                property_type=c_prop_i.property_type,
                output_format=c_prop_i.datetime_format
            )

            employees_service.set_contact_parameters(c_prop_i, new_value)

        employees_service.do_update_or_create_contact_parameters(modified_by=contact.last_modified_name)

        # is_contact_photo - start
        if True:
            attachments = contact.attachments
            for attachment in attachments:
                if getattr(attachment, "is_contact_photo", False):
                    document_modified_time = SanitazerService.format_ewsdatetime_to_datetime(attachment.last_modified_time)
                    if employee_obj.document_modified_time is None or (employee_obj.document_modified_time and employee_obj.document_modified_time < document_modified_time):
                        filename = attachment.name or "contact_photo.jpg"
                        employee_obj.document_modified_time = document_modified_time
                        employee_obj.document.save(filename, ContentFile(attachment.content), save=False)
                        employee_obj.save(update_fields=["document", "document_modified_time"])
                    break
        # is_contact_photo - end

        # if not ignore_diff_properties:
        #     # return contact_email #TO-DO временно отключу апдейт в Привсерв
        #     changed_parameters = employees_service.get_all_changed_parameters_obj()
        #     if changed_parameters and len(changed_parameters) > 0:
        #         # from synchronization.services.SyncService import SyncService
        #         # # SyncService.handle_changed_properties(employee_obj=employee_obj.id, changed_properties_exchange=diff_properties)
        #         # SyncService.handle_changed_properties_exchange(employee_obj=employee_obj, changed_properties_exchange=changed_parameters)
        #         from synchronization.services.SyncInstantService import SyncInstantService
        #         SyncInstantService.handle_changed_properties_exchange(employee_obj=employee_obj, changed_properties_exchange=changed_parameters)

        return contact_email

    # +++++++++++OLD CODE
    #             contacts_parameters_obj, created = Contacts_Parameters.objects.get_or_create(
    #                 contacts_parameters=c_prop_i,
    #                 # name=property_name_str,
    #                 contacts=contacts_obj,
    #                 defaults={
    #                     "contacts_parameters": c_prop_i,
    #                     # "name": property_name_str,
    #                     "value": new_value,
    #                     "contacts": contacts_obj
    #                 }
    #             )
    #             if created:
    #                 current_properties_in_db_arr[property_name_str] = None
    #             else:
    #                 current_properties_in_db_arr[property_name_str] = contacts_parameters_obj.value
    #                 if contacts_parameters_obj.value != new_value:
    #                     contacts_parameters_obj.value = new_value
    #                     contacts_parameters_obj.save(update_fields=["value", "updated_at"])
    #
    #             new_properties_from_aws_arr[property_name_str] = new_value
    #
    #         if not ignore_diff_properties:
    #             diff_properties = {}
    #             for key in current_properties_in_db_arr.keys() & new_properties_from_aws_arr.keys():
    #                 if current_properties_in_db_arr[key] != new_properties_from_aws_arr[key]:
    #                     diff_properties[key] = new_properties_from_aws_arr[key]
    #
    #             if diff_properties and len(diff_properties) > 0:
    #                 print(diff_properties)
    #
    #                 # from synchronization.services.SyncService import SyncService
    #                 # SyncService.handle_changed_properties(contact_exchange_id=contacts_obj.id, changed_properties_exchange=diff_properties)
    #
    #         del current_properties_in_db_arr, new_properties_from_aws_arr

    @staticmethod
    def generate_monthly_datetime_ranges(start_date_str="2018-06-01 00:00:00"):
        if start_date_str is None:
            start_date_str = "2018-06-01 00:00:00"
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
        end_date = datetime.now() + timedelta(days=5)

        date_arr = []

        while start_date < end_date:
            from_date = start_date

            next_month = start_date.month + 1
            year = start_date.year + (next_month - 1) // 12
            next_month = (next_month - 1) % 12 + 1

            # to_date = start_date.replace(year=year, month=next_month) - timedelta(seconds=1)
            to_date = start_date.replace(year=year, month=next_month)

            if to_date > end_date:
                to_date = end_date

            to_date_plus_minutes = to_date + timedelta(minutes=1)

            date_arr.append({
                'from': from_date.strftime("%Y-%m-%d %H:%M:%S"),
                'to': to_date_plus_minutes.strftime("%Y-%m-%d %H:%M:%S")
            })

            start_date = to_date

        return date_arr
