from django.views import View
from exchangelib import Credentials, Account, Contact, ExtendedProperty, EWSDateTime, Configuration, DELEGATE
from django.http import JsonResponse
from datetime import datetime
import json
import pytz
import random, traceback
import time


privser_primary_smtp_address = "ES.com"
privser_username = "ESom"
privser_password = "aSY"
folder_path = "Conest"


credentials = Credentials(username=privser_username, password=privser_password)
configuration = Configuration(server=privser_primary_smtp_address, credentials=credentials)

account = Account(
    primary_smtp_address=privser_primary_smtp_address,
    credentials=credentials,
    config=configuration,
    autodiscover=True,
    access_type=DELEGATE
)

contacts_folder = account.contacts
public_folders_root = account.public_folders_root
folder = public_folders_root
for i in folder_path.split("/"):
    folder = folder / i


user_email = "Test20@Automation.com"
user_email2 = "Test10@Automation.com"


property_name_str = "Test 3"
class CustomExtendedProperty(ExtendedProperty):
    property_set_id = "00020329-0000-0000-C000-000000000046"
    # property_tag = 0x881A001F
    property_name = property_name_str
    property_type = "String"

Contact.register(property_name_str, CustomExtendedProperty)




property_name_str2 = "Test 333"
class CustomExtendedProperty(ExtendedProperty):
    property_set_id = "00020329-0000-0000-C000-000000000046"
    # property_tag = 0x881A001F
    property_name = property_name_str2
    property_type = "String"

Contact.register(property_name_str2, CustomExtendedProperty)






contact_item = folder.get(email_addresses = user_email)
contact_item2 = folder.get(email_addresses = user_email2)


custom_value = getattr(contact_item, property_name_str, None)
print(f"OLD {property_name_str} Value  ----->>>>>>>>>>   : {custom_value}")

custom_value = getattr(contact_item, property_name_str2, None)
print(f"OLD {property_name_str2} Value2  ----->>>>>>>>>>   : {custom_value}")

custom_value = getattr(contact_item2, property_name_str, None)
print(f"OLD {property_name_str} Value  ----->>>>>>>>>>   : {custom_value}")

custom_value = getattr(contact_item2, property_name_str2, None)
print(f"OLD {property_name_str2} Value2  ----->>>>>>>>>>   : {custom_value}")

print(f"last_modified_name: ", contact_item.last_modified_name)
print(f"last_modified_time: ", contact_item.last_modified_time)


setattr(contact_item, property_name_str, "T-32")
contact_item.save(update_fields=[property_name_str])

custom_value = getattr(contact_item, property_name_str, None)
print(f"NEW Property Value  ----->>>>>>>>>>   : {custom_value}")

print(f"last_modified_name: ", contact_item.last_modified_name)
print(f"last_modified_time: ", contact_item.last_modified_time)

