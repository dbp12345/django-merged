from operator import attrgetter
from exchangelib import HTMLBody
from exchangelib.errors import ErrorIrresolvableConflict, DoesNotExist
from exchangelib.indexed_properties import PhoneNumber, EmailAddress

from company.models import Employees
from core.services.SanitazerService import SanitazerService
from exchange.services.ExchangeService import ExchangeService


class ExchangeApiService(ExchangeService):
    @staticmethod
    def update_exc_contact_by_email_with_data(email: str, data, ignore_diff_properties: bool = False):
        """
        :param email:
        :param data:
        :return:
        """
        # TO-DO Мы не будем обновлять пока данные в старой папке, а в новой надо создавать нового сотрудника
        # from core.exceptions import StopTask
        # from synchronization.models import Sync_Delivery_Logs
        # raise StopTask("Update logic disabled", status_code=Sync_Delivery_Logs.StatusCode.CANCELED.value)
        if not isinstance(data, dict):
            return

        property_name_list = list(data.keys())
        ExchangeService.contact_register_and_get_all_properties(property_name_list=property_name_list)


        try:
            try:
                contact_exc = ExchangeService.find_user_by_email(contact_exc_email=email)
            except DoesNotExist:
                updated = Employees.objects.filter(email=email, created_in_exchange=0).update(created_in_exchange=1)
                if updated:
                    contact_exc = ExchangeService.create_contact_with_email(email_address=email)
                else:
                    from time import sleep
                    sleep(2)
                    contact_exc = ExchangeService.find_user_by_email(contact_exc_email=email)

            ExchangeApiService.__update_exc_contact(contact_item=contact_exc, data=data)
        except Exception:
            raise

        finally:
            ExchangeService.contact_deregister_properties(property_name_list)

    @staticmethod
    def __update_exc_contact(contact_item, data):
        from exchange.models import Contacts_Prop
        for property_name, new_property_value in data.items():
            contacts_prop_obj = Contacts_Prop.objects.get(property_name=property_name)

            if property_name == "MobilePhone":
                property_name = "phone_numbers"
                old_value_from_exchange = getattr(contact_item, property_name, None) or []
                old_value_exclude_current_phone = [phone for phone in old_value_from_exchange if phone.label != "MobilePhone"]
                if new_property_value:
                    new_property_value = [
                        PhoneNumber(label="MobilePhone", phone_number=new_property_value),
                    ]
                    new_property_value = old_value_exclude_current_phone + new_property_value
                    new_property_value.sort(key=attrgetter('label'))
                else:
                    new_property_value = old_value_exclude_current_phone
                    new_property_value.sort(key=attrgetter('label'))

            elif property_name == "Email":
                property_name = "email_addresses"
                old_value_from_exchange = getattr(contact_item, property_name, None) or []
                old_value_exclude_current_email = [email for email in old_value_from_exchange if email.label != "EmailAddress1"]
                if new_property_value:
                    new_property_value = [
                        EmailAddress(label="EmailAddress1", email=new_property_value),
                    ]
                    new_property_value = old_value_exclude_current_email + new_property_value
                    new_property_value.sort(key=attrgetter('label'))
                else:
                    new_property_value = old_value_exclude_current_email
                    new_property_value.sort(key=attrgetter('label'))

            elif property_name == "text_body":
                property_name = "body"
                new_property_value = HTMLBody(f"<html><body><pre>{new_property_value}</pre></body></html>")

            # Если в названии поля есть phone, то редактируем значение
            # if "phone" in property_name:
            #     old_value_from_exchange = SanitazerService.format_phone_sanitize_to_str(old_value_from_exchange)
            #     new_property_value = SanitazerService.format_phone_sanitize_to_str(new_property_value)

            if property_name not in ("phone_numbers", "email_addresses"):
                new_property_value = SanitazerService.normalize_to_str_by_property_type_for_exchange(
                    value=new_property_value,
                    property_type=contacts_prop_obj.property_type
                )

            if property_name != "body":
                try:
                    setattr(contact_item, property_name, new_property_value)
                    contact_item.save(update_fields=[property_name])
                except Exception as e:
                    from core.exceptions import StopTask
                    from synchronization.models import Sync_Delivery_Logs
                    raise StopTask(str(e), status_code=Sync_Delivery_Logs.StatusCode.EXTERNAL_API_ERROR.value)
                # try:
                #     contact_item.save(update_fields=[property_name])
                # except ErrorIrresolvableConflict:
                #     # Обновляем контакт и пробуем снова
                #     fresh_item = contact_item.account.contacts.get(id=contact_item.id)
                #     setattr(fresh_item, property_name, new_property_value)
                #     fresh_item.save(update_fields=[property_name])
                #     contact_item = fresh_item  # обновляем локальную переменную на актуальную
                #     raise
