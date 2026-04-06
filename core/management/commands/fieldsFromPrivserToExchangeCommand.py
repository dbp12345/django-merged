from django.core.management.base import BaseCommand
from privser.models import Contacts_Parameters

from synchronization.services.SyncInstantService import SyncInstantService


# python manage.py fieldsFromPrivserToExchangeCommand
class Command(BaseCommand):
    help = "Run fieldsFromPrivserToExchangeCommand"

    def add_arguments(self, parser):
        parser.add_argument(
            "--after_date",
            type=str,
            help="Specify the start date and time in the format YYYY-MM-DD HH:MM:SS",
        )

    def handle(self, *args, **options):
        # Просто делаю это с локалки...
        #
        # Отключить ненужные методы из обработчика:
        # 1.
        # def generate_entities_from_contact_params(self, employee: Employees):
        #     return
        # 2.
        # def handle_changed_properties_exchange(
        #         employee_obj,
        #         changed_properties_exchange: dict = None
        # ):
        #     return
        # 3.
        # # UPDATE IN PRIVSER:

        # # S-130 Online Component
        # contacts_parameters_obj = Contacts_Parameters.objects.filter(name="3V0WKqUoQWpmRVxk22Aj")
        # print("contacts_parameters_obj.count() = ", contacts_parameters_obj.count())
        # for contacts_parameters_i in contacts_parameters_obj:
        #     print("user.email", contacts_parameters_i.contacts.email)
        #     print("value", contacts_parameters_i.value)
        #     SyncInstantService.handle_changed_properties_privser(
        #         contact_privser_obj=contacts_parameters_i.contacts,
        #         changed_properties_privser={contacts_parameters_i.name: contacts_parameters_i.value}
        #     )

        # # S-190 Webinar
        # contacts_parameters_obj = Contacts_Parameters.objects.filter(name="mZJGsMEbif9YzSVLEICl")
        # print("contacts_parameters_obj.count() = ", contacts_parameters_obj.count())
        # for contacts_parameters_i in contacts_parameters_obj:
        #     print("user.email", contacts_parameters_i.contacts.email)
        #     print("value", contacts_parameters_i.name)
        #     print("value", contacts_parameters_i.value)
        #     SyncInstantService.handle_changed_properties_privser(
        #         contact_privser_obj=contacts_parameters_i.contacts,
        #         changed_properties_privser={contacts_parameters_i.name: contacts_parameters_i.value}
        #     )

        # # L-180 Webinar
        # contacts_parameters_obj = Contacts_Parameters.objects.filter(name="1pFn5QQKFCbR4UiC2ysC")
        # print("contacts_parameters_obj.count() = ", contacts_parameters_obj.count())
        # for contacts_parameters_i in contacts_parameters_obj:
        #     print("user.email", contacts_parameters_i.contacts.email)
        #     print("value", contacts_parameters_i.name)
        #     print("value", contacts_parameters_i.value)
        #     SyncInstantService.handle_changed_properties_privser(
        #         contact_privser_obj=contacts_parameters_i.contacts,
        #         changed_properties_privser={contacts_parameters_i.name: contacts_parameters_i.value}
        #     )

        # # RT-130 Webinar 2023
        # contacts_parameters_obj = Contacts_Parameters.objects.filter(name="qkEA5LI53NtGF2vk22LK")
        # print("contacts_parameters_obj.count() = ", contacts_parameters_obj.count())
        # for contacts_parameters_i in contacts_parameters_obj:
        #     print("user.email", contacts_parameters_i.contacts.email)
        #     print("value", contacts_parameters_i.name)
        #     print("value", contacts_parameters_i.value)
        #     SyncInstantService.handle_changed_properties_privser(
        #         contact_privser_obj=contacts_parameters_i.contacts,
        #         changed_properties_privser={contacts_parameters_i.name: contacts_parameters_i.value}
        #     )

        # # RT-130 Webinar 2024
        # contacts_parameters_obj = Contacts_Parameters.objects.filter(name="TyiuTJjGkL2HTODMqyJt")
        # print("contacts_parameters_obj.count() = ", contacts_parameters_obj.count())
        # for contacts_parameters_i in contacts_parameters_obj:
        #     print("user.email", contacts_parameters_i.contacts.email)
        #     print("value", contacts_parameters_i.name)
        #     print("value", contacts_parameters_i.value)
        #     SyncInstantService.handle_changed_properties_privser(
        #         contact_privser_obj=contacts_parameters_i.contacts,
        #         changed_properties_privser={contacts_parameters_i.name: contacts_parameters_i.value}
        #     )

        # # RT-130 Webinar 2025
        # contacts_parameters_obj = Contacts_Parameters.objects.filter(name="WQnFngSJ7ObFTTD0Zn7k")
        # print("contacts_parameters_obj.count() = ", contacts_parameters_obj.count())
        # for contacts_parameters_i in contacts_parameters_obj:
        #     print("user.email", contacts_parameters_i.contacts.email)
        #     print("value", contacts_parameters_i.name)
        #     print("value", contacts_parameters_i.value)
        #     SyncInstantService.handle_changed_properties_privser(
        #         contact_privser_obj=contacts_parameters_i.contacts,
        #         changed_properties_privser={contacts_parameters_i.name: contacts_parameters_i.value}
        #     )


        print("END")
        exit()
