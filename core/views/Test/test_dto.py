from django.views import View
from exchangelib import Credentials, Account, Contact, ExtendedProperty, EWSDateTime, Configuration, DELEGATE
from django.http import JsonResponse
from datetime import datetime
import json
import pytz
import random, traceback
import time

from core.dto.customExtendedProperty import ExtendedPropertyDTO


privser_primary_smtp_address = "ES.com"
privser_username = "ESer.com"
privser_password = "aY"
folder_path = "ContTest"





def get_custom_extended_property(dto: ExtendedPropertyDTO):
    credentials = Credentials(username=privser_username, password=privser_password)
    configuration = Configuration(server=privser_primary_smtp_address, credentials=credentials)

    account = Account(
        primary_smtp_address=privser_primary_smtp_address,
        credentials=credentials,
        config=configuration,
        autodiscover=True,
        access_type=DELEGATE
    )

    # contacts_folder = account.contacts
    public_folders_root = account.public_folders_root
    folder = public_folders_root
    for i in folder_path.split("/"):
        folder = folder / i
    print(dto.property_name)
    class CustomExtendedProperty(ExtendedProperty):
        property_set_id = dto.property_set_id
        # property_tag = 0x3A16
        property_name = dto.property_name
        property_type = dto.property_type

    Contact.register(dto.attr_name, CustomExtendedProperty)

    contact_item = folder.get(email_addresses="Test20@Automation.com")

    custom_value = getattr(contact_item, "Test 333", None)
    print(f"OLD Property Value  ----->>>>>>>>>>   : {custom_value}")

    #SET
    setattr(contact_item, "Test 333", "5-lm")
    contact_item.save(update_fields=["Test 333"])

    #GET
    custom_value = getattr(contact_item, "Test 333", None)
    print(f"NEW Property Value  ----->>>>>>>>>>   : {custom_value}")

def setCustomExtendedProperty():
    setattr(contact_item, "Test 333", "5-lm")
    contact_item.save(update_fields=["Test 333"])






# property_set_id = "00020329-0000-0000-C000-000000000046"
# # property_tag = 0x3A16
# property_name = "Test 3"
# property_type = "String"
# attr_name = "custom_property"


property_set_id = "00020329-0000-0000-C000-000000000046"
# property_tag = 0x3A16
property_name = "Test 333"
property_type = "String"
attr_name = "custom_property"

dtoEP = ExtendedPropertyDTO(property_set_id, property_name, property_type, attr_name)

get_custom_extended_property(dtoEP)





