import logging
import re

from company.models import Employees
from paychex.services.PaychexAPIService import PaychexAPI


class PaychexService:
    @staticmethod
    def split_phone(phone: str):
        digits = re.sub(r"\D", "", phone)
        number = digits[-7:] if len(digits) >= 7 else None
        area = digits[-10:-7] if len(digits) >= 10 else None
        country = digits[:-10] if len(digits) >= 11 else None
        return country, area, number

    @staticmethod
    def create_progress_worker_in_paychex(employee: Employees):
        country, area, number = PaychexService.split_phone(employee.get_phone or "")

        worker_data = [
            {
                "workerType": "EMPLOYEE",
                # "sex": "NOT_SPECIFIED",
                # "employmentType": "FULL_TIME",
                # "exemptionType": "NON_EXEMPT",
                # "birthDate": "2000-04-22T00:00:00Z",
                # "hireDate": "2024-04-22T00:00:00Z",
                # "workState": "OR",
                "name": {
                    "familyName": employee.get_param_value("last_name") or "",
                    "middleName": employee.get_param_value("middle_name") or "",
                    "givenName": employee.get_param_value("first_name") or ""
                },
                # "legalId": {
                #     "legalIdType": "SSN",
                #     "legalIdValue": "234567890"
                # },
                # "currentStatus": {
                #     "workerStatusId": "00DWS906IMW2JSH8AQK2",
                #     "statusType": "PENDING_EMPLOYMENT",
                #     "statusReason": "PENDING_HIRE",
                #     "effectiveDate": "2025-04-22"
                # },
                # "locationId": "1060039934748789",
                # "organization": {
                #     "organizationId": "1070061612875206"
                # },
                "communications": [
                    {
                        "type": "EMAIL",
                        "usageType": "PERSONAL",
                        # "usageType": "BUSINESS",
                        "uri": employee.get_email or ""
                    },
                    {
                        "type": "MOBILE_PHONE",
                        "usageType": "BUSINESS",
                        "dialCountry": country,
                        "dialArea": area,
                        "dialNumber": number,
                    },
                ]
            }
        ]

        # return JsonResponse(worker_data, safe=False)

        api = PaychexAPI()
        api.authenticate()
        # res = api.get_companies()
        company_id = "004UWBZQLAK1M9E3QGHF"
        # res = api.get_company(company_id)

        res = api.add_in_progress_worker(company_id, worker_data)
        print("worker_data", worker_data)
        logger = logging.getLogger("my_log")
        logger.error(
            "\n================ PaychexAPI.add_in_progress_worker ================\n"
            f"User_email    : {employee.email}\n"
            f"response   : {res}\n"
        )
        # res = api.get_worker_statuses(company_id)
        # res = api.get_company_jobs(company_id)

        # res = api.get_company_workers(company_id=company_id)
        # res = api.get_worker(worker_id=employee_id)
        # res = api.get_worker_communications(worker_id=employee_id)
        # res = api.get_company_locations(company_id=company_id)

        # print(res)
        return res
