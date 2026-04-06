import json
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.timezone import now
from exchangelib import ExtendedProperty
from exchangelib.errors import DoesNotExist
from exchangelib.indexed_properties import EmailAddress

from company.models import Employees, Employees_Parameters, FireRun
from company.services.EmployeesService import EmployeesService
from core.tasks import update_from_privser_task
from exchange.models import Contacts_Prop
from paychex.services import PaychexCompanyWorkersService
from paychex.services.PaychexAPIService import PaychexAPI
from privser.models import Request_To_Privser
from privser.services.PrivserAPI2Service import PrivserAPI2Service
from privser.services.PrivserAPIService import PrivserAPIService
from privser.services.PrivserService import PrivserService
from django.contrib import messages
from core.tasks import generate_entities_from_contact_params_task

# python manage.py myTestCommand


class Command(BaseCommand):
    help = "Run myTestCommand"

    def add_arguments(self, parser):
        parser.add_argument(
            "--param",
            type=str,
            help="Param",
        )

    def handle(self, *args, **options):
        # aa = {
        # "25958",
        # }
        #
        #
        for obj in Employees.objects.iterator():
            print(obj.id)
            if settings.DEBUG:
                generate_entities_from_contact_params_task.run(employee_id=obj.id)
            else:
                generate_entities_from_contact_params_task.delay(employee_id=obj.id)
        
        exit()

        api = PaychexAPI()
        api.authenticate()

        # если у тебя уже есть oauth token для payroll — не важно, TWS использует свой токен
        punches = api.get_time_punches_for_employee(emp_identifier="2171", start_date="2025-10-01T00:00:00Z", end_date="2025-10-13T23:59:59Z")
        print(punches)
        exit()

        # "paycheckId": "004WOHNWMFQ2NIMU6DPQ"
        # "workerId": "00M9LQF7M3YXZ85Q005D",

        # result = api.get_company_workers(company_id = "004UWBZQLAK1M9E3QGHF", limit = 1, offset=0)
        # result = api.get_company_pay_period(company_id = "004UWBZQLAK1M9E3QGHF", payperiod_id="1070080855174191")

        # content = result.get("content")
        #
        # for i in content:
        #     workerId = i.get("workerId")
        #     hireDate = i.get("hireDate")
        #     name = i.get("name")
        #     familyName = name.get("familyName")
        #     middleName = name.get("middleName")
        #     givenName = name.get("givenName")
        #
        #     print(workerId, hireDate, familyName, middleName, givenName)



        result = api.get_companies()
        # result = api.get_company_pay_periods(from_date="2025-05-12T00:00:00Z", to_date="2050-01-01T00:00:00Z")
        # result = api.get_worker(worker_id="00M9LQF7M3DLYQ7TYTKO")
        # result = api.get_worker_communications(worker_id="00M9LQF7M3DLYQ7TYTKO")
        # result = api.get_worker_checks(worker_id="00M9LQF7M3DLYQ7TYTKO", payperiodid="1070075668090970")
        result = api.get_companies_checks(pay_period_id="1080039803285891")
        formatted_result = json.dumps(result, indent=4, ensure_ascii=False)
        print(formatted_result)
        exit()

        # for obj in FireRun.objects.all():
        #     val = (obj.hotline_in_remarks or "").strip().upper()
        #     if val == "Y":
        #         obj.hotline_in_remarks_bool = True
        #     elif val == "N":
        #         obj.hotline_in_remarks_bool = False
        #     else:
        #         obj.hotline_in_remarks_bool = None
        #     obj.save(update_fields=["hotline_in_remarks_bool"])


        exit()

        # Если работает `.users`
        try:
            message.users.add(user)
        except AttributeError:
            # Fallback если используется через recipients
            message.recipients.create(user=user)



        exit()

        users = User.objects.filter(is_staff=True)

        # Message.objects.create_for_users(
        #     users=users,
        #     content="Только для персонала!",
        #     level=40  # error
        # )

        message = Message.objects.create(
            content="Тестовое сообщение!",
            level=Message.INFO_LEVEL,  # Или SUCCESS_LEVEL, WARNING_LEVEL, DANGER_LEVEL
            begins=now(),
            # begins=timezone.now(),
            # expires=now() + timedelta(days=30),
            modified_by="admin2233",  # Или кто угодно
        )


        for user in users:
            message.add(user)  # <== вот это критично

        # contacts_privser_isinstance = ContactsPrivser.objects.all()
        #
        # for contact_privser in contacts_privser_isinstance:
        #     print(contact_privser.contact_id)
        #
        #     update_from_privser_task.apply_async(
        #         kwargs={
        #             "contact_id": contact_privser.contact_id,
        #             "ignore_diff_properties": False,
        #         },
        #         countdown=360  # timeout 6 min
        #     )

        # EmployeesService.generate_entities_from_contact_params(employee_id=49482)

        exit()

        param = options.get("param")

        from exchange.services.ExchangeService import ExchangeService

        try:
            contact_exc = ExchangeService.find_user_by_email(contact_exc_email="jadingeorge321@gmail2.com")
        except DoesNotExist:
            print("Не нашли в эксч")

        print("contact_exc: ", contact_exc)
        exit()

        # Запуск для делания обьектов из параметров. Можно запускать много раз...
        # Сделать для этого отделюную команду даже!
        # if param:
        #     print(param)
        #     EmployeesService.generate_entities_from_contact_params(employee_id=param)
        #     # EmployeesService.generate_entities_from_contact_params(employee_id=25975)
        # else:
        #     for e in Employees.objects.all():
        #         print(e.id)
        #         EmployeesService.generate_entities_from_contact_params(employee_id=e.id)
        #         # generate_entities_from_contact_params_task(employee_id = e.id)

        # надо пробовать сделать обновление параметров по каждому сотруднику
        if param:
            emails = Employees.objects.filter(id=param).values_list("email", flat=True).distinct()
            for i, email in enumerate(emails):
                update_by_email_task.apply_async(
                    kwargs={"email": email, "ignore_diff_properties": True},
                    countdown=i  # 1 секунда между задачами (i * 1)
                )
        else:
            emails = Employees.objects.exclude(email__isnull=True).exclude(email="").values_list("email", flat=True).distinct()
            for i, email in enumerate(emails):
                # update_by_email_task.apply_async(
                #     kwargs={"email": email, "ignore_diff_properties": True}
                # )
                update_by_email_task.apply_async(
                    kwargs={"email": email, "ignore_diff_properties": True},
                    countdown=i  # 1 секунда между задачами (i * 1)
                )
        

        


        print("DONEEEEEEEEEEEEEE")

        exit()

        employees_service = EmployeesService()
        employee_obj, _ = employees_service.update_or_create_contact(
            contact_id="rrrrrrrrrr",
            email="aaaaaa@ddd.fff",
            last_modified_name="myTestCommand",
            last_modified_time=datetime.now().astimezone(),
            datetime_created=datetime.now().astimezone(),
        )

        exit()

        # Filter: 17
        # Selected
        # fields: ['499', '510', '520', '540', '553', '680', '463', '483', '495', '684', '580', '590']
        # exc_to_privser
        # 17['499', '510', '520', '540', '553', '680', '463', '483', '495', '684', '580', '590']

        # sync_employees_task.run("exc_to_privser", 17, ['499', '510', '520', '540', '553', '680', '463', '483', '495', '684', '580', '590'])
        #
        #
        # print("DONE")
        # exit()

        # employee = Employees.objects.get(id=46791)
        # EmployeesService.handle_contact_params(employee=employee)

        # generate_entities_from_contact_params_task.run(employee_id=46791)
        #
        # exit()

        # AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAaHKYJgAAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAA=  :tyflo310@gmail.com
        # AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAaHKZl5AAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAA=  :l0gancarpenter@icloud.com
        # AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAaHKZl7AAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAA=  :eggsontoast889@gmail.com
        # AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAaHKZo/AAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAA=  :tyflo310@gmail.com
        # AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAaHKZo+AAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAA=  :bradyfire05@gmail.com
        # AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAaHKZpAAAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAA=  :cooper.c.petersen@gmail.com
        # AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAaHKZpEAAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAA=  :graceslynnsia@gmail.com
        # AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAaHKZpLAAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAA=  :angelacostaa710@gmail.com
        # AQIARgAAAxpEc5CqZhHNm8gAqgAvxFoJAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAADy7w6A6MWMTKhQqDM7ARKlAAaHKZpPAAAALgAAAxpEc5CqZhHNm8gAqgAvxFoDAPLvDoDoxYxMqFCoMzsBEqUAAAHG5kMAAAA=  :hclukey256@gmail.com






        # Message.objects.create(
        #     subject="Система обновлена",
        #     message="Все могут проверить новые возможности.",
        #     level="success",
        #     is_persistent=True,
        # )

        # exit()


        from exchange.services.ExchangeService import ExchangeService
        from exchange.services.ExchangeUpdatesService import ExchangeUpdatesService
        # contact_exc = ExchangeService.find_user_by_email(contact_exc_email="tyflo310@gmail.com")
        # contact_exc = ExchangeService.find_user_by_email(contact_exc_email="jakefarlee@gmail.com")
        # contact_exc = ExchangeService.find_user_by_email(contact_exc_email="bradyfire05@gmail.com")
        # contact_exc = ExchangeService.find_user_by_email(contact_exc_email="test11@automation.com")
        contact_exc = ExchangeService.find_user_by_email(contact_exc_email="dmytro.svietnoi@gmail.com")


        print(contact_exc)
        exit()




        last_modified_time = datetime(2026, 2, 3, 15, 50).astimezone()
        employees_service = EmployeesService()

        # employee = Employees.objects.get(email="test10@automation.com")
        employee = Employees.objects.get(id=242)

        exit()

        contacts_prop_objs = Contacts_Prop.objects.get(id=29)

        existing_objs = Employees_Parameters.objects.get(
            contacts_prop=contacts_prop_objs,
            employee=employee
        )

        existing_objs.value = "Fgjsfdsafl2222 asjdfhdslfh"
        existing_objs.save()

        exit()


        # data = PrivserAPI2Service().get_locations()
        # olV8ESTkIxjTCdPD9peS
        # privser_api2_service = PrivserAPI2Service()
        # data = PrivserAPI2Service().get_contacts_by_id(contact_id="zI21Z99EggoL7ejK4xw5")
        # data = PrivserAPI2Service().get_contacts_by_email(email="danewilkarson4@gmail.com")
        # contact_response = privser_api2_service.get_contacts_by_id("6DXwmz5rUKwCArsHus87")

        # formatted_result = json.dumps(data, indent=4, ensure_ascii=False)
        # print(formatted_result)
        # exit()

        # res = PrivserUpdatesService.update_all_fields_from_contact_id("VyY8HCnSJPJa4g6vZdTF")
        # res = PrivserUpdatesService.update_all_fields_from_contact_id("gzdkSyYB0O2X0MzK5OOX")

        # formatted_response = json.dumps(res, indent=4, ensure_ascii=False)
        # print(formatted_response)
        # print(res)
        # exit()

        api = PaychexAPI()
        api.authenticate()

        # result = api.get_company_workers(company_id = "004UWBZQLAK1M9E3QGHF", limit = 4)
        result = api.get_company_pay_periods(company_id="004UWBZQLAK1M9E3QGHF", status="PROCESSED", from_date="2024-05-12T00:00:00Z",
                                             to_date="2025-05-12T00:00:00Z")
        # result = api.get_worker_checks(worker_id="00M9LQF7M3DLYQ7TYTKO")
        formatted_result = json.dumps(result, indent=4, ensure_ascii=False)
        print(formatted_result)
        exit()

        for worker in result.get("content"):
            print("___")
            print("name: ", worker.get("name").get("familyName"), worker.get("name").get("middleName"), worker.get("name").get("givenName"))
            print("birthDate: ", worker.get("birthDate"))
            print("status: ", worker.get("currentStatus").get("statusType"))
            print("workerId: ", worker.get("workerId"))

        exit()

        """
        name:  Svietnoi None Dmytro
        birthDate:  1982-05-12T00:00:00Z
        status:  ACTIVE
        workerId:  00M9LQF7M3DLYQ7TYTKO
        
        """

        exit()

        # Добавить сотрудника
        worker_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
        }
        new_worker = api.add_worker(worker_data)
        print("Новый сотрудник:", new_worker)

        # Создать платёжную ведомость
        payroll_data = {
            "employees": [
                {"id": new_worker["id"], "hours": 40, "rate": 25.0}
            ],
            "pay_period": {"start": "2025-01-01", "end": "2025-01-15"},
            "pay_date": "2025-01-20",
        }
        payroll = api.create_payroll(payroll_data)
        print("Созданная платёжная ведомость:", payroll)

        exit()

        TestAllFieldsService.set_all_identified_fields_to_exchange_new()
        exit()

        account = ExchangeService.get_exchange_account()
        public_folders_root = account.public_folders_root

        contacts_shared_db = public_folders_root / 'Contasts Shared DB'
        chloe_test_folder = contacts_shared_db / 'ChloeTest'

        class DispatchCenterField(ExtendedProperty):
            property_name = "Dispatch Center"
            property_set_id = "00020329-0000-0000-C000-000000000046"
            property_type = "String"

        """
Tag: 0x8367001F
Type: PT_UNICODE
DASL: http://schemas.microsoft.com/mapi/string/{00020329-0000-0000-C000-000000000046}/Dispatch Center
Named Prop Name: Dispatch Center
Named Prop Guid: {00020329-0000-0000-C000-000000000046} = PS_PUBLIC_STRINGS
        """

        from exchangelib.items import Contact  # Импорт модели контакта
        Contact.register('dispatch_center', DispatchCenterField)

        for contact in chloe_test_folder.filter():  # Выбираем все контакты из папки
            if contact.display_name == "Test7 Automation":
                contact.im_addresses = None
                contact.dispatch_center = 'Value-7777'
                contact.email_addresses = [EmailAddress(label="EmailAddress1", email="default@example.com")]
                contact.save()

        exit()

    def handle3(self, *args, **options):

        privser_service = PrivserService()
        privser_api_service = PrivserAPIService()

        # user_id = "sZmDH4ccGYCrYZiIYDf5"
        # user_email = "test9@automation.com"

        # data = privser_api_service.get_contacts()
        # data = privser_api_service.update_contact()
        # data = privser_api_service.get_custom_fields()
        # data = privser_api_service.get_custom_fields_by_user("olV8ESTkIxjTCdPD9peS")
        # data = privser_api_service.get_contacts_by_query("owenburge2@gmail.com")
        # data = privser_api_service.get_contact_id_from_email("Test10@Automation.com")
        #
        # formatted_response = json.dumps(data, indent=4, ensure_ascii=False)
        # print(data)
        # print(formatted_response)
        exit()

        # contacts_in_progres = Contacts.objects.filter(status_code=Contacts.StatusCode.IN_PROGRESS)
        # contacts_in_progres = privser_service.get_contacts_in_progres()

        # contact = Contacts.objects.get(
        #     id=22024
        # )

        request_to_privser = Request_To_Privser.objects.get(
            id=51
        )

        # privser_service.create_request_to_privser_from_contact(contact)
        privser_service.handle_request_to_privser(request_to_privser)

        self.stdout.write(self.style.SUCCESS("Done") + "\n")

    def handle2(self, *args, **options):
        # exchange_service = ExchangeService()

        # request_to_exchange = Request_To_Exchange.objects.get(
        #     id=20
        # )
        # exchange_service.handle_request_to_exchange(request_to_exchange)

        # request_to_exchange_all = Request_To_Exchange.objects.filter(
        #     status_code=Request_To_Exchange.StatusCode.NEW
        # )
        #
        # request_to_exchange_all = Request_To_Exchange.objects.all()

        # for request_to_exchange in request_to_exchange_all:
        #     print(request_to_exchange.id)
        #     exchange_service.handle_request_to_exchange(request_to_exchange)
        #     # time.sleep(2)

        exit()
