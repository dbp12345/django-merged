from datetime import datetime
from django.conf import settings
from django.db import transaction

from company.models import Employees
from company.services.EmployeesService import EmployeesService
from core.models.EmployeeLastUpdates import ApiType
from privser.services.PrivserAPI2Service import PrivserAPI2Service
from privser.services.PrivserService import PrivserService
from core.tasks.privser_tasks import update_from_privser_task


class PrivserUpdatesService(PrivserService):

    # python manage.py runUpdateFromPrivserCommand
    # --ignore_diff_properties --param1=1736483338535 --param2=OtWswXHyrpyYuwpe3mzt
    @staticmethod
    def get_and_update_all_fields_for_all_contacts(
        param1: str = None,
        param2: str = None,
        query: dict = None,
        ignore_diff_properties: bool = False,
    ):
        privser_api2_service = PrivserAPI2Service()

        if param1 is not None and param2 is not None:
            if query:
                query.update({"searchAfter": [param1, param2]})
            else:
                query = {"searchAfter": [param1, param2]}

        print("query:", query)

        response = privser_api2_service.search_contacts(query, page_limit=100)

        # try:
        #     len(response.get("contacts"))
        # except Exception as e:
        #     print("except len(contacts), REPEAT")
        #     PrivserUpdatesService.get_and_update_all_fields_for_all_contacts(
        # param1=param1, param2=param2, ignore_diff_properties=ignore_diff_properties)

        if len(response.get("contacts")) == 0:
            print("len(contacts)=0")
            return

        for i in response.get("contacts"):
            # PrivserUpdatesService.update_all_fields_from_contact_id(i.get('id'), ignore_diff_properties)
            if settings.DEBUG:
                PrivserUpdatesService.update_all_fields_from_contact_id(
                    i.get("id"), ignore_diff_properties
                )
            else:
                update_from_privser_task.apply_async(
                    kwargs={
                        "contact_id": i.get("id"),
                        "ignore_diff_properties": ignore_diff_properties,
                    },
                    countdown=360,  # timeout 6 min
                )

            # query = i.get("searchAfter")
            param1 = i.get("searchAfter")[0]
            param2 = i.get("searchAfter")[1]

        # print(query)

        PrivserUpdatesService.get_and_update_all_fields_for_all_contacts(
            param1=param1,
            param2=param2,
            query=query,
            ignore_diff_properties=ignore_diff_properties,
        )
        return

        # contact_response = result.get("contacts", [])[0]
        # PrivserUpdatesService.update_all_fields_from_contact(
        # contact_response=contact_response, ignore_diff_properties=ignore_diff_properties)

        # group(
        #     update_from_privser_task.si(contact=contact, ignore_diff_properties=ignore_diff_properties)
        #     for contact in result.get("contacts", [])
        # )().get(timeout=43200)

        # group_tasks = group(
        #     update_from_privser_task.si(
        # contact_response=contact_response, ignore_diff_properties=ignore_diff_properties)
        #     for contact_response in result.get("contacts", [])
        # )
        # group_tasks.apply_async()
        #
        # # for contact in result.get("contacts", []):
        # #     update_from_privser_task.delay(contact=contact, ignore_diff_properties=ignore_diff_properties)
        #
        # next_page_url = result.get("meta", {}).get("nextPageUrl")
        # if next_page_url:
        #     print("total: ", result.get("meta", {}).get("total"))
        #     print("nextPageUrl: ", result.get("meta", {}).get("nextPageUrl"))
        #     print("currentPage: ", result.get("meta", {}).get("currentPage"))
        #     print("prevPage: ", result.get("meta", {}).get("prevPage"))
        #     parsed_url = urlparse(next_page_url)
        #     query = parsed_url.query
        #     print("query: ", query)
        #     PrivserUpdatesService.get_and_update_all_fields_for_all_contacts(
        # query=query, ignore_diff_properties=ignore_diff_properties)

    @staticmethod
    def do_update_from_privser_by_last_modified_time(
        task=True, ignore_diff_properties: bool = False
    ) -> list[str]:

        # task = False

        list_of_changed_emails = []
        date_updated_str = EmployeesService.get_employee_last_updates(
            type_api=ApiType.PRIVSER
        ).date_updated_str

        last_modified_contacts = (
            PrivserUpdatesService.get_last_modified_contacts_by_time(
                datetime_str_after=date_updated_str
            )
        )
        from privser.models import Contacts as ContactsPrivser

        for contact_i in last_modified_contacts:
            contact_privser_instance = ContactsPrivser.objects.filter(
                contact_id=contact_i["id"]
            ).first()

            # Если не нашли, то применяем все diff_properties
            if not contact_privser_instance:
                ignore_diff_properties = False

            # PrivserUpdatesService.update_all_fields_from_contact_id(contact_i.get('id'), ignore_diff_properties)
            if settings.DEBUG:
                update_from_privser_task.run(
                    **{
                        "contact_id": contact_i.get("id"),
                        "ignore_diff_properties": ignore_diff_properties,
                    }
                )
            else:
                update_from_privser_task.apply_async(
                    kwargs={
                        "contact_id": contact_i.get("id"),
                        "ignore_diff_properties": ignore_diff_properties,
                    }
                )

        PrivserUpdatesService.set_last_modified_date_from_contacts(
            last_modified_contacts
        )
        return list_of_changed_emails

    # @staticmethod
    # def get_last_modified_time_from_db():
    #     return Contacts.objects.latest("date_updated").date_updated

    @staticmethod
    def get_last_modified_contacts_by_time(
        datetime_str_after, datetime_before_str=None
    ):
        privser_api2_service = PrivserAPI2Service()
        query = {
            "filters": [
                {
                    "field": "dateUpdated",
                    "operator": "range",
                    "value": {
                        "gt": datetime_str_after,
                        # "lt": "2025-02-21T00:00:00.000Z"
                    },
                }
            ]
        }

        response = privser_api2_service.search_contacts(query, page_limit=100)

        return response.get("contacts", [])

    @staticmethod
    def set_last_modified_date_from_contacts(contacts):
        if not contacts:
            return
        latest_contact = max(
            contacts, key=lambda x: datetime.fromisoformat(x["dateUpdated"].rstrip("Z"))
        )
        EmployeesService.save_or_update_employee_last_updates(
            contact_id=latest_contact["id"],
            type_api=ApiType.PRIVSER,
            date_updated_str=latest_contact["dateUpdated"],
        )

    @staticmethod
    def update_all_fields_from_contact(
        contact_response, ignore_diff_properties: bool = False
    ):
        fields_arr = PrivserService.get_all_fields_from_contact_response(
            contact_response
        )
        PrivserUpdatesService.save_or_update_contacts_from_arr(
            fields_arr, ignore_diff_properties
        )
        PrivserUpdatesService.save_or_update_contacts_photos_from_arr(fields_arr, False)

    @staticmethod
    def update_all_fields_from_contact_id(
        contact_id, ignore_diff_properties: bool = False
    ):
        if contact_id is None:
            raise ValueError("Contact_ID cannot be None")
        # privser_service = PrivserService()
        privser_api2_service = PrivserAPI2Service()

        contact_response = privser_api2_service.get_contacts_by_id(contact_id)
        fields_arr = PrivserService.get_all_fields_from_contact_response(
            contact_response
        )
        # response = privser_api2_service.get_all_notes(contact_id)
        # # note_text = privser_service.all_notes_to_str_from_res(response)
        # # fields_arr["Notes"] = note_text
        # note_list = privser_service.all_notes_to_list_from_res(response)
        # fields_arr["Notes"] = note_list
        # Это для апдейта картинок
        res = PrivserUpdatesService.save_or_update_contacts_from_arr(
            fields_arr, ignore_diff_properties
        )
        PrivserUpdatesService.save_or_update_contacts_photos_from_arr(fields_arr, False)
        return res

    # @staticmethod
    # def update_all_fields_from_contact_email(contact_email, ignore_diff_properties: bool = False):
    #     if contact_email is None:
    #         return contact_email
    #     from privser.services.PrivserAPI2Service import PrivserAPI2Service
    #     privser_api2_service = PrivserAPI2Service()
    #     contact_response = privser_api2_service.get_contacts_by_email(contact_email)
    #     contact_response = privser_api2_service.get_contacts_by_id(contact_response.get("id"))
    #     fields_arr = PrivserService.get_all_fields_from_contact_response(contact_response)
    #     return PrivserUpdatesService.save_or_update_contacts_from_arr(fields_arr, ignore_diff_properties)

    @staticmethod
    def save_or_update_contacts_from_arr(
        fields_arr, ignore_diff_properties: bool = False
    ) -> str:
        contact_id = fields_arr.pop("id")
        email = fields_arr.get("email", None)
        fields_arr.pop("searchAfter", None)  # just delete as unnecessary

        if not email:
            from core.exceptions import StopTask
            from synchronization.models import Sync_Delivery_Logs

            raise StopTask(
                "Column 'email' is null",
                status_code=Sync_Delivery_Logs.StatusCode.CANCELED.value,
            )

        last_activity_seconds = fields_arr.pop("lastActivity", 946684800000) / 1000
        last_activity = datetime.fromtimestamp(last_activity_seconds).astimezone()
        date_updated = fields_arr.pop("dateUpdated")

        from privser.models import Contacts as ContactsPrivser

        contacts_obj, created = ContactsPrivser.objects.update_or_create(
            contact_id=contact_id,
            defaults={
                "email": email,
                "date_updated": date_updated,
                "last_activity": last_activity,
            },
        )

        # это просто можно удалить. Это делает повторный save
        if created:
            contacts_obj.test = 644
        else:
            contacts_obj.test = 645

        contacts_obj.save(update_fields=["test"])

        # current_properties_in_db_arr = {}
        # new_properties_from_aws_arr = {}
        changes = {}
        from privser.models import Contacts_Parameters
        from synchronization.services.SyncDeliveryService import SyncDeliveryService
        from synchronization.models import Sync_Delivery_Logs
        from privser.models import Custom_Fields
        from core.tasks import handle_sync_delivery_log_task
        from django.db.models import Q

        for key, value in fields_arr.items():
            try:
                obj, created = Contacts_Parameters.objects.get_or_create(
                    name=key, contacts=contacts_obj, defaults={"value": value}
                )
                changes[obj] = value  # это я буду всегда обновлять теперь!
            except Exception:
                obj, created = Contacts_Parameters.objects.get_or_create(
                    name=key, contacts=contacts_obj, defaults={"value": "ERROR_TEXT"}
                )
                obj.value = "ERROR_TEXT"
                obj.save(update_fields=["value", "updated_at"])
                continue

            if created:
                changes[obj] = value
            elif str(obj.value) != str(value):
                try:
                    obj.value = value
                    obj.save(update_fields=["value", "updated_at"])
                except Exception:
                    obj.value = "ERROR_TEXT"
                    obj.save(update_fields=["value", "updated_at"])
                changes[obj] = value

        employees_service = EmployeesService()

        employee = Employees.objects.filter(contact_id=contact_id).first()

        if not employee:
            employee = (
                Employees.objects.filter(email=email)
                .filter(Q(contact_id__isnull=True) | Q(contact_id=email))
                .first()
            )
            if employee:
                employee.contact_id = contact_id
                employee.save(update_fields=["contact_id", "updated_at"])

        if employee:
            employees_service.set_contact(employee_obj=employee)
        else:
            employee, created = employees_service.update_or_create_contact(
                contact_id=contact_id,
                email=email,
                last_modified_name="privser",
                last_modified_time=last_activity,
                datetime_created=date_updated,
            )

        for contacts_parameters_i, param_value in changes.items():

            custom_field = Custom_Fields.objects.filter(
                Q(privser_id=contacts_parameters_i.name)
                | Q(privser_name=contacts_parameters_i.name)
            ).first()

            # if custom_field and custom_field.exchange_property and not custom_field.no_sync:
            # print("contacts_prop_obj: ", contacts_prop_obj)
            # print("param_value: ", param_value)

            try:
                employees_service.set_contact_parameters(
                    custom_field.exchange_property, param_value
                )
            except Exception:
                # todo
                print(
                    f"[WARNING] No contacts_prop_obj found for: {contacts_parameters_i.name}"
                )

        employees_service.do_update_or_create_contact_parameters()
        changed_parameters = employees_service.get_all_changed_parameters_obj()
        old_parameters = employees_service.get_old_parameters_obj()

        # print("changed_parameters", changed_parameters)
        # print("old_parameters", old_parameters)

        sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
            employee=employee,
            changed_parameters=changed_parameters,
            old_parameters=old_parameters,
            target_system=Sync_Delivery_Logs.TargetSystemChoices.EXCHANGE,
            modified_by=f"from privser {date_updated}",
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

        return email

    @staticmethod
    def save_or_update_contacts_photos_from_arr(
        fields_arr, ignore_diff_properties: bool = False
    ) -> str:
        import requests
        import os
        from django.core.files.base import ContentFile
        from company.models import Employees
        from company.models import Employees_Pictures

        field_map = {
            "G0MIEOY6M6QiManeaWw7": "photo_privser_cropped_picture_for_red_card",
            "XZi0yimkN2ekjYv8tauC": "photo_privser_passport_picture",
            "Et6He1FIsCiSDwZecZuQ": "photo_privser_picture_at_field_training",
        }

        email = fields_arr.pop("email", None)
        if not email:
            return "No email provided"

        employee_instance = Employees.objects.filter(email=email).first()
        if not employee_instance:
            return "Employee not found"

        employees_pictures_instance, _ = Employees_Pictures.objects.get_or_create(
            employee=employee_instance
        )

        for api_fieldname, model_fieldname in field_map.items():
            if api_fieldname not in fields_arr:
                continue

            images_dict = fields_arr[api_fieldname]

            if not isinstance(images_dict, dict) or not images_dict:
                continue

            file_identifier, image_entry = next(
                iter(images_dict.items())
            )  # <-- получаем и ID файла
            if not isinstance(image_entry, dict):
                continue

            url = image_entry.get("url")
            if not url:
                continue

            # Проверка: если уже есть файл — пропускаем
            # existing_field = getattr(employees_pictures_instance, model_fieldname)
            # if existing_field and existing_field.name:
            #     continue

            # Скачиваем файл
            response = requests.get(url)
            if response.status_code == 200:
                # Формируем имя файла через UUID
                original_name = image_entry.get("meta", {}).get("originalname")
                extension = (
                    os.path.splitext(original_name)[1] if original_name else ".jpg"
                )
                filename = f"{file_identifier}{extension}"

                content = ContentFile(response.content)
                getattr(employees_pictures_instance, model_fieldname).save(
                    filename, content, save=False
                )

        employees_pictures_instance.save()
        return email
