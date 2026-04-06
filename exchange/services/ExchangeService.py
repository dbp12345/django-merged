from django.utils.timezone import localtime
from exchangelib import Credentials, Account, Configuration, ExtendedProperty, DELEGATE, Contact, NTLM
from exchangelib.indexed_properties import EmailAddress
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
import warnings
from urllib3.exceptions import InsecureRequestWarning
from exchangelib.errors import UnauthorizedError, ErrorServerBusy, MultipleObjectsReturned, DoesNotExist
from django.conf import settings

from exchange.models import Contacts_Prop

warnings.simplefilter("ignore", InsecureRequestWarning)
BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter

exchange_primary_smtp_address = settings.EXCHANGE_PRIMARY_SMTP_ADDRESS
exchange_username = settings.EXCHANGE_USERNAME
exchange_password = settings.EXCHANGE_PASSWORD
property_set_id_conf = settings.EXCHANGE_PROPERTY_SET_ID_CONF
folder_path = settings.EXCHANGE_FOLDER_PATH

class ExchangeService:
    ignore_register_property_list = [
        "job_title",
        "given_name",
        "middle_name",
        "surname",
        "display_name",
        "MobilePhone",
        "Email",
        "text_body",
        "file_as",
        "file_as_mapping",
    ]

    @staticmethod
    def contact_register_property(property_name_to_set, property_type_to_set):
        if not hasattr(Contact, property_name_to_set):
            class ContactRegisterExtendedProperty(ExtendedProperty):
                property_set_id = property_set_id_conf
                property_name = property_name_to_set
                property_type = property_type_to_set

            Contact.register(property_name_to_set, ContactRegisterExtendedProperty)
        return


    @staticmethod
    def contact_register_and_get_all_properties(**kwargs):
        property_name_list = kwargs.get('property_name_list')
        if property_name_list:
            contacts_prop_db = Contacts_Prop.objects.filter(
                property_name__in=property_name_list,
                property_type__in=[
                    Contacts_Prop.TypeChoices.SYSTEM_TIME,
                    Contacts_Prop.TypeChoices.STRING,
                    Contacts_Prop.TypeChoices.DOUBLE,
                ]
            )
        else:
            contacts_prop_db = Contacts_Prop.objects.filter(
                property_type__in=[
                    Contacts_Prop.TypeChoices.SYSTEM_TIME,
                    Contacts_Prop.TypeChoices.STRING,
                    Contacts_Prop.TypeChoices.DOUBLE,
                ]
            )
        contacts_prop_list = []
        for c_prop_i in contacts_prop_db:
            property_name_str = c_prop_i.property_name
            property_type_str = c_prop_i.property_type
            property_set_id_str = property_set_id_conf
            # property_set_id_str = c_prop_i.property_set_id #from DB

            if property_name_str not in ExchangeService.ignore_register_property_list:
                contacts_prop_list.append(c_prop_i)

                if not hasattr(Contact, property_name_str):
                    class CustomExtendedProperty(ExtendedProperty):
                        property_set_id = property_set_id_str
                        # property_tag = 0x881A001F
                        property_name = property_name_str
                        property_type = property_type_str

                    Contact.register(property_name_str, CustomExtendedProperty)

        return contacts_prop_list

    @staticmethod
    def contact_deregister_all_properties():
        contacts_prop_db = Contacts_Prop.objects.filter()
        for c_prop_i in contacts_prop_db:
            ExchangeService.contact_deregister_properties(c_prop_i.property_name)

    # @staticmethod
    # def get_exchange_account():
    #     credentials = Credentials(username=exchange_username, password=exchange_password)
    #     configuration = Configuration(server=exchange_primary_smtp_address, credentials=credentials)
    #
    #     try:
    #         account = Account(
    #             primary_smtp_address=exchange_primary_smtp_address,
    #             credentials=credentials,
    #             config=configuration,
    #             autodiscover=True,
    #             access_type=DELEGATE
    #         )
    #         return account
    #     except UnauthorizedError as e:
    #         raise RuntimeError("-== Failed to log in. Check your credentials. ==-") from e

    @staticmethod
    def get_exchange_account():
        credentials = Credentials(username=exchange_username, password=exchange_password)
        configuration = Configuration(
            server="mail.privser.com",
            credentials=credentials,
            auth_type=NTLM
        )

        try:
            account = Account(
                primary_smtp_address=exchange_primary_smtp_address,
                credentials=credentials,
                config=configuration,
                autodiscover=False,
                access_type=DELEGATE
            )
            return account
        except UnauthorizedError as e:
            raise RuntimeError("-== Failed to log in. Check your credentials. ==-") from e

    @staticmethod
    def get_exchange_folder(folder_path_extra = None):
        if folder_path_extra:
            folder_path_var = folder_path_extra
        else:
            folder_path_var = folder_path

        account = ExchangeService.get_exchange_account()

        for attempt in range(3):
            try:
                public_folders_root = account.public_folders_root
                break
            except ErrorServerBusy as e:
                if attempt == 2:
                    raise
                import time
                time.sleep(2 ** attempt)  # экспоненциальный бэкофф: 1, 2, 4 сек
        else:
            raise RuntimeError("Exchange public_folders_root unavailable after 3 retries")

        folder = public_folders_root
        for i in folder_path_var.split("/"):
            folder = folder / i
        return folder

    @staticmethod
    def contact_deregister_properties(property_name_arr):
        for property_name in property_name_arr:
            if property_name not in ExchangeService.ignore_register_property_list:
                if hasattr(Contact, property_name):
                    Contact.deregister(property_name)

    @staticmethod
    def find_user_by_email(contact_exc_email=None, folder = None):
        if not folder:
            folder = ExchangeService.get_exchange_folder()
        try:
            return folder.get(email_addresses=EmailAddress(label="EmailAddress1", email=contact_exc_email))
        except MultipleObjectsReturned:
            # TO-DO: ОГРОМНЫЙ АЛЕРТ что дублей по email — это беда
            print(f"[ALERT] Multiple contacts found for email: {contact_exc_email}")
            raise
        except DoesNotExist:
            # TO-DO remove this
            import logging
            logger = logging.getLogger("my_info")
            logger.error(
                f"DoesNotExist           : {contact_exc_email}\n"
            )
            print(f"find_user_by_email: DoesNotExist - {contact_exc_email}")
            raise
        except Exception as e:
            raise


    @staticmethod
    def create_contact_with_email(email_address: str):
        from exchangelib.indexed_properties import EmailAddress
        from core.services.SanitazerService import SanitazerService
        from django.utils import timezone
        folder = ExchangeService.get_exchange_folder()
        contact = Contact(
            folder=folder,
            email_addresses=[
                EmailAddress(label="EmailAddress1", email=email_address)
            ],
            display_name=email_address,
            file_as_mapping = "LastCommaFirst",
            last_modified_time = SanitazerService.datetime_to_ewsdatetime(localtime(timezone.now()))
        )
        contact.save()
        return contact

    @staticmethod
    def find_fields_by_user(contact_exc):
        for field in dir(contact_exc):
            if not field.startswith('_'):  # Исключаем скрытые методы и атрибуты
                print("___")
                print(f"{field}: {getattr(contact_exc, field, None)}")

    @staticmethod
    def get_total_contacts():
        folder = ExchangeService.get_exchange_folder()
        return folder.all().count()


"""
subject="Dmyt Svie - Dust Busters Plus, LLC",
sensitivity="Normal",
text_body="\r\n\r\n",
body="<html>\r\n<head>\r\n<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\r\n<meta name="Generator" content="Microsoft Exchange Server">\r\n<!-- converted from rtf -->\r\n<style><!-- .EmailQuote { margin-left: 1pt; padding-left: 4pt; border-left: #800000 2px solid; } --></style>\r\n</head>\r\n<body>\r\n<font face="Calibri" size="2"><span style="font-size:11pt;">\r\n<div>&nbsp;</div>\r\n<div>&nbsp;</div>\r\n</span></font>\r\n</body>\r\n</html>\r\n",
attachments=[],
datetime_received=EWSDateTime(2024, 11, 25, 19, 58, 30, tzinfo=EWSTimeZone(key="UTC")),
size=7721,
importance="Normal",
is_submitted=False,
is_draft=False,
is_from_me=False,
is_resend=False,
is_unmodified=False,
datetime_sent=EWSDateTime(2024, 11, 25, 19, 58, 30, tzinfo=EWSTimeZone(key="UTC")),
datetime_created=EWSDateTime(2024, 11, 25, 19, 59, 24, tzinfo=EWSTimeZone(key="UTC")),
reminder_is_set=False,
reminder_minutes_before_start=0,
has_attachments=False,
Driver's License Expiration Date="5/6/2025",
culture="en-US",
effective_rights=EffectiveRights(create_associated=False, create_contents=False, create_hierarchy=False, delete=False, modify=True, read=True, view_private_items=False),
last_modified_name="Exchange Sync",
last_modified_time=EWSDateTime(2024, 12, 4, 6, 29, 53, tzinfo=EWSTimeZone(key="UTC")),
is_associated=False,
web_client_read_form_query_string="https://mail.privser.com/owa?ItemID=AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAYBzq84AAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAA%3D&exvsurl=1&viewmodel=PersonaCardViewModelFactory",
conversation_id=ConversationId(id="AAQkAGNiZTMxOWU0LWNlMGMtNDk0Yy04N2ExLWMyMTM3YzAyNDdiZAAQAEKgpYbJc0skr4CAHWu131k=", changekey=None),
file_as="Svie, Dmytro",
file_as_mapping="LastCommaFirst",
display_name="Dmo Svi",
given_name="Dmytro",
initials="D.S.",
complete_name=CompleteName(title=None, first_name="Dmytro", middle_name=None, last_name="Svi", suffix=None, initials="D.S.", full_name="Dmy Sviei", nickname=None, yomi_first_name=None, yomi_last_name=None),
company_name="Dust Busters Plus, LLC",
email_addresses=[EmailAddress(label="EmailAddress1", email="dmyi@gml.cm")],
phone_numbers=[PhoneNumber(label="MobilePhone", phone_number="(541) 514-9017")],
im_addresses=[ImAddress(label="ImAddress1", im_address=None)],
job_title="Administrative Staff",
postal_address_index="None",
surname="Svi"
"""

"""
Contact(
mime_content=b'BEGIN:VCARD\r\nPROFILE:VCARD\r\nVERSION:3.0\r\nMAILER:Microsoft Exchange\r\nPRODID:Microsoft Exchange\r\nFN:Test10 Test-14 Test-12\r\nN:Test-12;Test10;Test-14;;\r\nEMAIL;TYPE=INTERNET:test10@automation.com\r\nNOTE:Test1\\n1111\\n99999\\n7777\\nArawt\\n\\n\r\nORG:;\r\nCLASS:PUBLIC\r\nADR;TYPE=WORK:;;;;;;\r\nADR;TYPE=HOME:;;;;;;\r\nADR;TYPE=POSTAL:;;;;;;\r\nTEL;TYPE=WORK:+1 (111) 222-7777\r\nTEL;TYPE=HOME:+1 (765) 571-1236\r\nTEL;TYPE=CELL:+1 (765) 571-1236\r\nTITLE:99966\r\nX-MS-IMADDRESS:\r\nCATEGORIES:Red Category\r\nREV;VALUE=DATE-TIME:2025-03-12T23:46:27,749Z\r\nEND:VCARD\r\n', _id=ItemId(id='AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAWiKldZAAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAA=', changekey='EQAAABYAAADy7w6A6MWMTKhQqDM7ARKlAAY6cBoK'), parent_folder_id=ParentFolderId(id='AQEuAAADGkRzkKpmEc2byACqAC/EWgMA8u8OgOjFjEyoUKgzOwESpQAAAcbmQwAAAA==', changekey='AQAAAA=='),
item_class='IPM.Contact.AllFields', subject='Test10 Test-14 Test-12', 
sensitivity='Normal', 
text_body='Test1\r\n1111\r\n99999\r\n7777\r\nArawt\r\n\r\n', 
body='<html>\r\n<head>\r\n<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\r\n<meta name="Generator" content="Microsoft Exchange Server">\r\n<!-- converted from rtf -->\r\n<style><!-- .EmailQuote { margin-left: 1pt; padding-left: 4pt; border-left: #800000 2px solid; } --></style>\r\n</head>\r\n<body>\r\n<font face="Courier New" size="3"><span style="font-size:12pt;">\r\n<div>Test1<br>\r\n\r\n1111<br>\r\n\r\n99999<br>\r\n\r\n7777<br>\r\n\r\nArawt</div>\r\n<div><font face="Calibri">&nbsp;</font></div>\r\n</span></font>\r\n</body>\r\n</html>\r\n', 
attachments=[], 
datetime_received=EWSDateTime(2024, 7, 3, 4, 24, 49, tzinfo=EWSTimeZone(key='UTC')), 
size=13935, 
categories=['Red Category'], 
importance='Normal', 
is_submitted=False, 
is_draft=False, 
is_from_me=False, 
is_resend=False, 
is_unmodified=False, 
datetime_sent=EWSDateTime(2024, 7, 3, 4, 24, 49, tzinfo=EWSTimeZone(key='UTC')), 
datetime_created=EWSDateTime(2024, 7, 3, 4, 21, 5, tzinfo=EWSTimeZone(key='UTC')), 
reminder_is_set=False, 
reminder_minutes_before_start=0, 
has_attachments=False, 
culture='en-US', 
effective_rights=EffectiveRights(create_associated=False, create_contents=False, create_hierarchy=False, delete=False, modify=True, read=True, view_private_items=False), 
last_modified_name='Exchange Sync', 
last_modified_time=EWSDateTime(2025, 3, 12, 23, 46, 27, tzinfo=EWSTimeZone(key='UTC')), 
is_associated=False, 
web_client_read_form_query_string='https://mail.privser.com/owa?ItemID=AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAWiKldZAAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAA%3D&exvsurl=1&viewmodel=ReadMessageItem', 
conversation_id=ConversationId(id='AAQkAGNiZTMxOWU0LWNlMGMtNDk0Yy04N2ExLWMyMTM3YzAyNDdiZAAQAKryXIZU3kbgqK1Ur5/mtfc=', changekey=None), 
file_as='Test-12, Test10 Test-14', 
file_as_mapping='LastCommaFirst', 
display_name='Test10 Test-14 Test-12', 
given_name='Test10', 
initials='T.T.T.', 
middle_name='Test-14', 
complete_name=CompleteName(title=None, first_name='Test10', middle_name='Test-14', last_name='Test-12', suffix=None, initials='T.T.T.', full_name='Test10 Test-14 Test-12', nickname=None, yomi_first_name=None, yomi_last_name=None), 
email_addresses=[EmailAddress(label='EmailAddress1', email='test10@automation.com')], 
phone_numbers=[PhoneNumber(label='BusinessPhone', phone_number='+1 (111) 222-7777'), 
PhoneNumber(label='HomePhone', phone_number='+1 (765) 571-1236'), 
PhoneNumber(label='MobilePhone', phone_number='+1 (765) 571-1236')], 
im_addresses=[ImAddress(label='ImAddress1', im_address=None)], 
job_title='99966', 
postal_address_index='None', 
surname='Test-12'
)
"""
