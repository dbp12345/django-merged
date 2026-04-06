from datetime import datetime
from urllib.parse import unquote

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils.text import get_valid_filename

from company.models import Employees_Parameters, Employee_Change_Queue
from company.services.TagEmployeesService import TagEmployeesService
from core.services.ManifestService import ManifestService
from core.tasks import check_possibility_firecrew_task
from exchange.models import Contacts_Prop
import logging

from privser.models import Contacts as ContactsPrivser
from privser.services.PrivserAPI2Service import PrivserAPI2Service

PROP_MAP = {
    "Email": "email",
}


def sync_employee_core_fields_from_param(instance: Employees_Parameters):
    try:
        prop_name = instance.contacts_prop.property_name
        model_field = PROP_MAP.get(prop_name)
        if not model_field:
            return

        employee = instance.employee
        # if not employee or not employee.id or not Employees.objects.filter(id=employee.id).exists():
        #     return

        updated_fields = []

        # Проверяем, остался ли параметр в БД
        param_exists = Employees_Parameters.objects.filter(
            employee=employee,
            contacts_prop=instance.contacts_prop
        ).exists()

        if not param_exists:
            setattr(employee, model_field, None)
            updated_fields.append(model_field)
        else:
            param_value = (instance.value or "").strip()
            current_value = (getattr(employee, model_field) or "").strip()

            # if prop_name == "Email" and param_value:
            #     param_value = get_unique_email(param_value, employee.contact_id, exclude_employee_id=employee.id)

            if param_value != current_value:
                setattr(employee, model_field, param_value)
                updated_fields.append(model_field)
                # # Меняем емеил и для привсер таблицы:
                # from privser.models import Contacts
                # contact_privser_qs = Contacts.objects.filter(email=current_value).filter()
                # if contact_privser_qs.exists():
                #     contact_privser_obj = contact_privser_qs.first()
                #     contact_privser_obj.email = param_value
                #     contact_privser_obj.save(update_fields=["email"])
                # Тут создаем или меняем Privser_Contact
                # if prop_name == "Email":
                #     from privser.models import Contacts
                #     with transaction.atomic():
                #         if current_value:
                #             if not Contacts.objects.filter(email=param_value).exists():
                #                 Contacts.objects.filter(email=current_value).update(email=param_value)
                #             else:
                #                 Contacts.objects.get_or_create(
                #                     email=param_value,
                #                     defaults={"contact_id": param_value},
                #                 )
                #         else:
                #             Contacts.objects.get_or_create(
                #                 email=param_value,
                #                 defaults={"contact_id": param_value},
                #             )

        if updated_fields:
            try:
                employee.save(update_fields=updated_fields)
            except Exception as e:
                logger = logging.getLogger("my_log")
                logger.error(f"[sync_param] save failed: employee_id={employee.id}, fields={updated_fields}, error={e}")
    except Exception as e:
        logger = logging.getLogger("my_log")
        logger.error(f"[sync_param] general error: {e}")


@receiver(post_save, sender=Employees_Parameters)
def sync_employees_parameters_on_save(sender, instance, created, **kwargs):
    sync_employee_core_fields_from_param(instance)
    try_send_employee_to_paychex_if_training_completed(instance)

    # contacts_prop_property_type = instance.contacts_prop.property_type
    contacts_prop_property_name = instance.contacts_prop.property_name
    if contacts_prop_property_name in ("Manifest Date, 2025", "Manifest Date"):
        transaction.on_commit(lambda: ManifestService.update_is_manifested_flags_from_all_dates(employee_id=instance.employee_id))

    if contacts_prop_property_name == "Not Eligible to Work (Button)":
        if instance.value_bool:
            if settings.DEBUG:
                check_possibility_firecrew_task.run(employee_id=instance.employee_id)
            else:
                transaction.on_commit(lambda employee_id=instance.employee_id: check_possibility_firecrew_task.delay(employee_id=employee_id))

    if contacts_prop_property_name == "Crew":
        if instance.value:
            if settings.DEBUG:
                check_possibility_firecrew_task.run(employee_id=instance.employee_id)
            else:
                transaction.on_commit(lambda employee_id=instance.employee_id: check_possibility_firecrew_task.delay(employee_id=employee_id))

    if contacts_prop_property_name == "tags":
        if instance.value_array:
            try:
                TagEmployeesService.replace_tags_for_employee(instance.employee, instance.value_array)
            except Exception:
                pass

    # if contacts_prop_property_type == Contacts_Prop.TypeChoices.DOCUMENT and instance.value:

    if created:
        create_change_queue(instance)
    else:
        old_value = Employees_Parameters.objects.filter(pk=instance.pk).values_list("value", flat=True).first()
        if old_value != instance.value:
            create_change_queue(instance)


@receiver(post_delete, sender=Employees_Parameters)
def sync_employees_parameters_on_delete(sender, instance, **kwargs):
    sync_employee_core_fields_from_param(instance)


@receiver(pre_save, sender=Employees_Parameters)
def process_value_type(sender, instance, **kwargs):
    if instance.contacts_prop.property_type == Contacts_Prop.TypeChoices.SYSTEM_TIME and instance.value:
        if isinstance(instance.value, datetime):
            instance.value_date = instance.value
            return
        try:
            from core.services.SanitazerService import SanitazerService
            parsed = SanitazerService.normalize_from_str_by_property_type(
                value=instance.value,
                property_type=instance.contacts_prop.property_type,
                output_format=instance.contacts_prop.datetime_format
            )
            if isinstance(parsed, datetime):
                instance.value_date = parsed
            else:
                instance.value_date = None
        except Exception:
            instance.value_date = None
    elif instance.contacts_prop.property_type == Contacts_Prop.TypeChoices.BOOL:
        if isinstance(instance.value, bool):
            instance.value_bool = instance.value
            return
        try:
            from core.services.SanitazerService import SanitazerService
            parsed = SanitazerService.normalize_from_str_by_property_type(
                value=instance.value,
                property_type=instance.contacts_prop.property_type,
            )
            if isinstance(parsed, bool):
                instance.value_bool = parsed
        except Exception:
            instance.value_bool = False


@receiver(post_save, sender=Employees_Parameters)
def save_document_from_value(sender, instance, created, **kwargs):
    try:
        if instance.contacts_prop.property_type != Contacts_Prop.TypeChoices.DOCUMENT:
            return
    except Exception:
        return


    if not instance.value and instance.value_file:
        # print("PUSH!PUSH!PUSH!PUSH!PUSH!PUSH!PUSH!")
        # print("________________________________________________")
        priv_cont = ContactsPrivser.objects.get(email=instance.employee.email)

        privser_api2_service = PrivserAPI2Service()
        try:
            privser_api2_service.upload_custom_field_file(
                contact_id=priv_cont.contact_id,
                field_id=instance.contacts_prop.custom_fields.privser_id,
                file_field=instance.value_file
            )
        except Exception:
            pass

    elif not instance.value and not instance.value_file:
        # Пока не придумал как удалять картинки удалённо. Потом подумаю..
        return
        print("del!!del!!del!!del!!del!!del!!del!!")
        print("________________________________________________")


        priv_cont = ContactsPrivser.objects.get(email=instance.employee.email)

        privser_api2_service = PrivserAPI2Service()
        try:
            privser_api2_service.upload_custom_field_file(
                contact_id=priv_cont.contact_id,
                field_id=instance.contacts_prop.custom_fields.privser_id,
                file_field=instance.value_file
            )
        except Exception:
            pass

    try:
        # value->value_file
        image_entry = instance.value
        if not image_entry or not isinstance(image_entry, dict):
            return

        url = image_entry.get("url")
        if not url:
            return

        originalname = image_entry.get("meta", {}).get("originalname")
        if originalname:
            originalname = get_valid_filename(unquote(originalname))

        if not originalname:
            return

        response = requests.get(url, stream=True, timeout=30)
        if response.status_code == 200:
            content = ContentFile(response.content)
            # сохраняем в storage, но не дергаем instance.save()
            getattr(instance, "value_file").save(originalname, content, save=False)

            # обновляем БД напрямую — чтобы не вызвать сигналы и не уйти в рекурсию
            Employees_Parameters.objects.filter(pk=instance.pk).update(
                value=None,
                value_file=instance.value_file.name
            )
    except Exception:
        # на ошибке не ломаем всё — чистим in-memory поле как у тебя было
        try:
            instance.value_file = None
        except Exception:
            pass


def try_send_employee_to_paychex_if_training_completed(instance: Employees_Parameters):
    if instance.contacts_prop.property_name == "Rating" and instance.value == "E":
        # print("Rating = E")
        from core.tasks.check_and_send_employee_to_paychex import check_and_send_employee_to_paychex
        check_and_send_employee_to_paychex.apply_async(
            args=[instance.employee.id],
            countdown=60  # 1 минута задержки
        )
        # check_and_send_employee_to_paychex(instance.employee.id)


def create_change_queue(instance: Employees_Parameters):
    Employee_Change_Queue.objects.create(
        employee=instance.employee,
        contacts_prop=instance.contacts_prop,
        new_value=instance.value
    )
