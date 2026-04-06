# https://developer.paychex.com/documentation
from django.conf import settings
from django.core.cache import cache
from http.client import RemoteDisconnected
import requests
import hashlib
import json


class PaychexAPI:
    company_id = None
    client_id = None
    client_secret = None
    base_url = None

    def __init__(self):
        self.company_id = settings.PAYCHEX_COMPANY_ID
        self.client_id = settings.PAYCHEX_CLIENT_ID
        self.client_secret = settings.PAYCHEX_CLIENT_SECRET
        self.base_url = settings.PAYCHEX_BASE_URL.rstrip("/")

        # instance state
        self.headers = {}
        self.access_token = None

        # simple requests session (no retries — per your request)
        self.session = requests.Session()
        self.request_timeout = None  # seconds

    def _cache_key(self):
        return f"paychex_access_token:{self.client_id}"

    def authenticate(self, force=False):
        """
        Get an OAuth2 token to access the API.
        Note: will store token in cache using expires_in exactly (no artificial buffer).
        """
        if not all([self.client_id, self.client_secret, self.base_url]):
            raise ValueError("Missing required configuration for Paychex API.")

        cache_key = self._cache_key()
        if not force:
            token = cache.get(cache_key)
            if token:
                self.access_token = token
                self.create_headers()
                return

        url = f"{self.base_url}/auth/oauth/v2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        # We intentionally do not swallow API errors — caller should see them.
        resp = self.session.post(url, headers=headers, data=data, timeout=self.request_timeout)
        # keep behavior: do not call resp.raise_for_status() here — let resp.json() or requests raise if needed
        token_data = resp.json()
        self.access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in")

        if not self.access_token or expires_in is None:
            # keep it explicit: if API didn't return token or expiry, raise
            raise RuntimeError("Authentication response missing access_token or expires_in")

        # store token in cache using exact expires_in from API (as you insisted)
        cache.set(cache_key, self.access_token, timeout=int(expires_in))
        self.create_headers()

    def create_headers(self):
        self.headers["Authorization"] = f"Bearer {self.access_token}"
        self.headers["Content-Type"] = "application/json"

    def _cache_request_key(self, method, url, params=None, json_body=None):
        """
        Create a deterministic cache key for requests.
        """
        key_src = {
            "method": method.upper(),
            "url": url,
            "params": params or {},
            "json": json_body or {},
        }
        j = json.dumps(key_src, sort_keys=True, default=str)
        return "paychex_resp:" + hashlib.sha256(j.encode()).hexdigest()

    def _request(self, method, url, **kwargs):
        if not self.access_token:
            self.authenticate()

        req_headers = kwargs.pop("headers", {})
        merged = {**self.headers, **req_headers, "Connection": "close"}

        resp = None
        try:
            resp = self.session.request(method, url, headers=merged, timeout=self.request_timeout, **kwargs)
            data = resp.json()
        except (requests.exceptions.ConnectionError, RemoteDisconnected) as e:
            # single recovery attempt
            try:
                self.session.close()
            except Exception:
                pass
            self.session = requests.Session()
            # force fresh token (in case server dropped session due to auth)
            try:
                self.authenticate(force=True)
            except Exception:
                raise
            resp = self.session.request(method, url, headers={**self.headers, "Connection": "close"}, timeout=self.request_timeout, **kwargs)
            data = resp.json()
        finally:
            if resp is not None:
                try:
                    resp.close()
                except Exception:
                    pass
        return data

    # --- API methods (unchanged signatures) ---
    def get_companies(self):
        url = f"{self.base_url}/companies"
        return self._request("GET", url)

    def get_company(self, company_id=None):
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}"
        return self._request("GET", url)

    def get_company_calculationbases(self, company_id=None):
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/calculationbases"
        return self._request("GET", url)

    def get_company_contacttypes(self, company_id=None):
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/contacttypes"
        return self._request("GET", url)

    def get_company_customfields(self, company_id=None):
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/customfields"
        return self._request("GET", url)

    def get_company_customfield(self, custom_field_id, company_id=None):
        if not company_id:
            company_id = self.company_id
        # fixed stray space in original implementation
        url = f"{self.base_url}/companies/{company_id}/customfields/{custom_field_id}"
        return self._request("GET", url)

    def get_company_organizations(self, company_id=None):
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/organizations"
        return self._request("GET", url)

    def get_company_locations(self, company_id=None):
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/locations"
        return self._request("GET", url)

    def get_company_workers(
            self,
            company_id=None,
            givenname=None,
            familyname=None,
            legallastfour=None,
            employeeid=None,
            from_date=None,
            to_date=None,
            locationid=None,
            offset=None,
            limit=None,
    ):
        """
        Получение списка работников компании через Paychex API.
        :param company_id: ID компании (обязательный параметр).
        :param givenname: Имя работника.
        :param familyname: Фамилия работника.
        :param legallastfour: Последние 4 цифры налогового ID.
        :param employeeid: ID работника.
        :param from_date: Дата начала периода поиска (ISO 8601).
        :param to_date: Дата окончания периода поиска (ISO 8601).
        :param locationid: ID локации.
        :param offset: Смещение для постраничного отображения.
        :param limit: Лимит на количество записей.
        :return: JSON с данными о работниках компании.
        """
        if not company_id:
            company_id = self.company_id
        params = {
            "givenname": givenname,
            "familyname": familyname,
            "legallastfour": legallastfour,
            "employeeid": employeeid,
            "from": from_date,
            "to": to_date,
            "locationid": locationid,
            "offset": offset,
            "limit": limit
        }
        params = {k: v for k, v in params.items() if v is not None}
        url = f"{self.base_url}/companies/{company_id}/workers"
        return self._request("GET", url, params=params)

    def get_worker(self, worker_id):
        url = f"{self.base_url}/workers/{worker_id}"
        return self._request("GET", url)

    def get_worker_communications(self, worker_id):
        url = f"{self.base_url}/workers/{worker_id}/communications"
        return self._request("GET", url)

    def get_worker_statuses(self, company_id=None):
        """
        Получение списка статусов работников компании через Paychex API.
        :param company_id: ID компании (обязательный параметр).
        :return: JSON с данными о статусах работников компании.
        """
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/workerstatuses"
        return self._request("GET", url)

    def get_worker_status(self, status_id, company_id=None):
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/workerstatuses/{status_id}"
        return self._request("GET", url)

    def add_in_progress_worker(self, worker_data, company_id=None):
        """
        Добавление работника в статусе "In Progress" через Paychex API.
        :param company_id: ID компании (обязательный параметр).
        :param worker_data: Данные о работнике в формате JSON.
        :return: JSON с ответом API.
        """
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/workers"
        response = requests.post(url, headers=self.headers, json=worker_data)

        # import http.client as http_client
        # http_client.HTTPConnection.debuglevel = 2
        # print("Response headers:")
        # for k, v in response.headers.items():
        #     print(f"{k}: {v}")
        # print("Response body:")
        # print(response.text)

        return response.json()

    def get_company_jobs(self, company_id=None, asof=None):
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/jobs"
        params = {}
        if asof:
            params["asof"] = asof
        return self._request("GET", url, params=params)

    def get_companies_checks(self, pay_period_id, company_id=None, offset=0, limit=0, filter_by_user_id=False):
        """
        Получение списка чеков компании.
        :param company_id: ID компании (обязательный параметр).
        :param pay_period_id: ID периода оплаты (обязательный параметр).
        :param offset: Смещение для постраничного отображения (необязательный параметр, по умолчанию 0).
        :param limit: Лимит на количество записей (необязательный параметр, по умолчанию 0).
        :param filter_by_user_id: Фильтрация по ID пользователя (необязательный параметр, по умолчанию False).
        :return: JSON с данными о чеках компании.
        """
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/checks"
        params = {
            "payperiodid": pay_period_id,
            "offset": offset,
            "limit": limit,
            "filterbyuserid": str(filter_by_user_id).lower(),
        }
        return self._request("GET", url, params=params)

    def add_company_check(self, check_data, company_id=None):
        """
        Добавление чека для работника через Paychex API.
        :param company_id: ID компании (обязательный параметр).
        :param check_data: Данные о чеке в формате JSON.
        :return: JSON с ответом API.
        """
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/checks"
        return self._request("POST", url, json=check_data)

    def get_company_pay_components(self, company_id=None, **params):
        """
        Получение списка компонентов оплаты компании через Paychex API.
        :param company_id: ID компании (обязательный параметр).
        :param params: Дополнительные параметры фильтрации:
            - effecttopay: Тип эффекта оплаты.
            - asof: Дата для фильтрации (ISO 8601).
            - classificationtype: Категория компонента.
            - name: Имя компонента.
        :return: JSON с ответом API.
        """
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/paycomponents"
        return self._request("GET", url, params=params)

    def get_company_pay_component(self, paycomponent_id, company_id=None, **params):
        """
        Получение информации о компоненте оплаты компании через Paychex API.
        :param company_id: ID компании (обязательный параметр).
        :param paycomponent_id: ID компонента оплаты (обязательный параметр).
        :param params: Дополнительные параметры фильтрации:
            - asof: Дата для фильтрации (ISO 8601).
        :return: JSON с ответом API.
        """
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/paycomponents/{paycomponent_id}"
        return self._request("GET", url, params=params)

    def get_company_pay_periods(self, company_id=None, status=None, from_date=None, to_date=None):
        """
        Получить список периодов оплаты для компании.

        :param company_id: str, ID компании
        :param status: list, список статусов (например, ["INITIAL", "PROCESSED"])
        :param from_date: str, начало диапазона дат (YYYY-MM-DD)
        :param to_date: str, конец диапазона дат (YYYY-MM-DD)
        :return: JSON с данными периодов оплаты
        """
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/payperiods"
        params = {}
        if status:
            params["status"] = status
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        return self._request("GET", url, params=params)

    def get_company_pay_period(self, payperiod_id, company_id=None):
        """
        Получение информации о конкретном периоде оплаты компании через Paychex API.
        :param company_id: ID компании (обязательный параметр).
        :param payperiod_id: ID периода оплаты (обязательный параметр).
        :return: JSON с ответом API.
        """
        if not company_id:
            company_id = self.company_id
        url = f"{self.base_url}/companies/{company_id}/payperiods/{payperiod_id}"
        return self._request("GET", url)

    def get_worker_checks(self, worker_id, **params):
        """
        Получение чеков для конкретного работника через Paychex API.
        :param worker_id: ID работника (обязательный параметр).
        :param params: Дополнительные параметры фильтрации:
            - payperiodid: ID периода оплаты (обязательный параметр).
            - filterbyuserid: Фильтрация по ID пользователя (boolean).
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/workers/{worker_id}/checks"
        return self._request("GET", url, params=params)

    def add_worker_check(self, worker_id, check_data):
        """
        Добавление чека для работника через Paychex API.
        :param worker_id: ID работника (обязательный параметр).
        :param check_data: Данные чека в формате JSON.
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/workers/{worker_id}/checks"
        return self._request("POST", url, json=check_data)

    def get_worker_check(self, worker_id, paycheck_id):
        """
        Получение информации о конкретном чеке работника через Paychex API.
        :param worker_id: ID работника (обязательный параметр).
        :param paycheck_id: ID чека (обязательный параметр).
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/workers/{worker_id}/checks/{paycheck_id}"
        return self._request("GET", url)

    def delete_worker_check(self, worker_id, paycheck_id):
        """
        Удаление чека работника через Paychex API.
        :param worker_id: ID работника (обязательный параметр).
        :param paycheck_id: ID чека (обязательный параметр).
        :return: None, если запрос успешен.
        """
        url = f"{self.base_url}/workers/{worker_id}/checks/{paycheck_id}"
        return self._request("DELETE", url)

    def delete_checks_by_payperiod_and_user(self, payperiod_id, deletebyuserid):
        """
        Удаление чеков по периоду оплаты и ID пользователя через Paychex API.
        :param payperiod_id: ID периода оплаты (обязательный параметр).
        :param deletebyuserid: Удаление по ID пользователя (обязательный параметр).
        :return: None, если запрос успешен.
        """
        url = f"{self.base_url}/checks"
        params = {"payperiodid": payperiod_id, "deletebyuserid": deletebyuserid}
        return self._request("DELETE", url, params=params)

    def add_pay_component_to_check(self, check_id, component_data):
        """
        Добавление компонента оплаты в чек через Paychex API.
        :param check_id: ID чека (обязательный параметр).
        :param component_data: Данные компонента оплаты в формате JSON.
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/checks/{check_id}/checkcomponents"
        return self._request("POST", url, json=component_data)

    def delete_pay_component_from_check(self, check_id, check_component_id):
        """
        Удаление компонента оплаты из чека через Paychex API.
        :param check_id: ID чека (обязательный параметр).
        :param check_component_id: ID компонента оплаты (обязательный параметр).
        :return: None, если запрос успешен.
        """
        url = f"{self.base_url}/checks/{check_id}/checkcomponents/{check_component_id}"
        return self._request("DELETE", url)

    def update_pay_component_in_check(self, check_id, check_component_id, component_data):
        """
        Обновление компонента оплаты в чеке через Paychex API.
        :param check_id: ID чека (обязательный параметр).
        :param check_component_id: ID компонента оплаты (обязательный параметр).
        :param component_data: Данные компонента оплаты в формате JSON.
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/checks/{check_id}/checkcomponents/{check_component_id}"
        return self._request("PATCH", url, json=component_data)


"""
# get_companies
{
    "metadata": {
        "contentItemCount": 1
    },
    "content": [
        {
            "companyId": "004UWBZQLAK1M9E3QGHF",
            "displayId": "16088691",
            "legalName": "DUST BUSTERS PLUS LLC",
            "hasPermission": true,
            "legalId": {
                "legalIdType": "FEIN",
                "legalIdValue": "320033641"
            },
            "communications": [
                {
                    "type": "PO_BOX_ADDRESS",
                    "usageType": "BUSINESS",
                    "postOfficeBox": "PO BOX 50370",
                    "city": "EUGENE",
                    "postalCode": "97405",
                    "countrySubdivisionCode": "OR",
                    "countryCode": "US"
                }
            ],
            "links": [
                {
                    "rel": "self",
                    "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF"
                },
                {
                    "rel": "workers",
                    "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/workers"
                }
            ]
        }
    ],
    "links": [
        {
            "rel": "self",
            "href": "https://api.paychex.com/companies/"
        }
    ]
}


# get_company
{
    "content": [
        {
            "companyId": "004UWBZQLAK1M9E3QGHF",
            "displayId": "16088691",
            "legalName": "DUST BUSTERS PLUS LLC",
            "hasPermission": true,
            "legalId": {
                "legalIdType": "FEIN",
                "legalIdValue": "320033641"
            },
            "communications": [
                {
                    "type": "PO_BOX_ADDRESS",
                    "usageType": "BUSINESS",
                    "postOfficeBox": "PO BOX 50370",
                    "city": "EUGENE",
                    "postalCode": "97405",
                    "countrySubdivisionCode": "OR",
                    "countryCode": "US"
                }
            ],
            "links": [
                {
                    "rel": "self",
                    "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF"
                },
                {
                    "rel": "workers",
                    "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/workers"
                }
            ]
        }
    ],
    "links": []
}


# get_company_calculationbases
{
    "metadata": {
        "contentItemCount": 44
    },
    "content": [
        {
            "calculationBaseId": "004UWBZQJESG217P6CK3",
            "calculationBaseName": "All earnings - tips - disability"
        },
        ...,
        {
            "calculationBaseId": "1f25a3d1-8262-44de-a7f8-075674ce02f3",
            "calculationBaseName": "Retirement ER Match"
        }
    ],
    "links": [
        {
            "rel": "self",
            "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/calculationbases"
        }
    ]
}


# get_company_contacttypes
{
    "content": [
        {
            "contactTypeId": "82450",
            "contactTypeName": "Emergency Contact",
            "relationshipTypes": [
                {
                    "relationshipTypeId": "458810",
                    "relationshipTypeName": "Spouse"
                },
                {
                    "relationshipTypeId": "458820",
                    "relationshipTypeName": "Parent"
                },
                {
                    "relationshipTypeId": "458830",
                    "relationshipTypeName": "Sibling"
                },
                {
                    "relationshipTypeId": "458840",
                    "relationshipTypeName": "Child"
                },
                {
                    "relationshipTypeId": "458740",
                    "relationshipTypeName": "Friend"
                },
                {
                    "relationshipTypeId": "458725",
                    "relationshipTypeName": "Domestic partner"
                },
                {
                    "relationshipTypeId": "458800",
                    "relationshipTypeName": "Other"
                }
            ]
        }
    ],
    "links": []
}


# get_company_customfields
{
    "metadata": {
        "contentItemCount": 0
    },
    "content": []
}


# get_company_workers
{
    "metadata": {
        "contentItemCount": 2,
        "pagination": {
            "offset": 0,
            "limit": 2,
            "itemCount": 2108,
            "total": 2108
        }
    },
    "content": [
        {
            "workerId": "004UWBZQLAT1SNBX8IRX",
            "employeeId": "717",
            "workerType": "EMPLOYEE",
            "exemptionType": "NON_EXEMPT",
            "workState": "OR",
            "birthDate": "1993-12-04T00:00:00Z",
            "sex": "MALE",
            "hireDate": "2018-08-06T00:00:00Z",
            "name": {
                "familyName": "Abrahamsen",
                "middleName": "T",
                "givenName": "Jonathan"
            },
            "legalId": {
                "legalIdType": "SSN",
                "legalIdValue": "542433996"
            },
            "laborAssignmentId": "1070061944834037",
            "locationId": "1070061682362150",
            "organization": {
                "organizationId": "1070061612875212",
                "name": "400 Shop",
                "number": "400"
            },
            "currentStatus": {
                "workerStatusId": "004UWBZQKMVOXG1R1SBF",
                "statusType": "TERMINATED",
                "statusReason": "VOLUNTARY___OTHER",
                "effectiveDate": "2022-10-31T00:00:00Z"
            },
            "links": [
                {
                    "rel": "self",
                    "href": "https://api.paychex.com/workers/004UWBZQLAT1SNBX8IRX"
                },
                {
                    "rel": "communications",
                    "href": "https://api.paychex.com/workers/004UWBZQLAT1SNBX8IRX/communications"
                }
            ]
        },
        {
            "workerId": "00M9LQF7LIJGXCVIMM16",
            "employeeId": "1675",
            "workerType": "EMPLOYEE",
            "exemptionType": "NON_EXEMPT",
            "workState": "OR",
            "birthDate": "1992-02-07T00:00:00Z",
            "sex": "NOT_SPECIFIED",
            "hireDate": "2023-06-05T00:00:00Z",
            "name": {
                "familyName": "Abrego",
                "middleName": "Antonio",
                "givenName": "Severiano"
            },
            "legalId": {
                "legalIdType": "SSN",
                "legalIdValue": "541396133"
            },
            "laborAssignmentId": "1070061944834037",
            "locationId": "1070061682362150",
            "organization": {
                "organizationId": "1070061612875206",
                "name": "100 Firefighters",
                "number": "100"
            },
            "currentStatus": {
                "workerStatusId": "004UWBZQKMVOXG1R1SBV",
                "statusType": "TERMINATED",
                "statusReason": "LACK_OF_WORK___END_OF_SEASON",
                "effectiveDate": "2023-10-12T00:00:00Z"
            },
            "links": [
                {
                    "rel": "self",
                    "href": "https://api.paychex.com/workers/00M9LQF7LIJGXCVIMM16"
                },
                {
                    "rel": "communications",
                    "href": "https://api.paychex.com/workers/00M9LQF7LIJGXCVIMM16/communications"
                }
            ]
        }
    ],
    "links": [
        {
            "rel": "self",
            "href": "https://api.paychex.com/workers/?companyid=004UWBZQLAK1M9E3QGHF&offset=0&limit=2"
        },
        {
            "rel": "next",
            "href": "https://api.paychex.com/workers/?companyid=004UWBZQLAK1M9E3QGHF&offset=2&limit=2"
        }
    ]
}

# get_worker_statuses
{
    "metadata": {
        "contentItemCount": 55
    },
    "content": [
        {
            "workerStatusId": "00DWS906IMW2JSH8AQJ9",
            "statusType": "ACTIVE",
            "statusReason": "HIRED"
        },
        {
            "workerStatusId": "00DWS906IMW2JSH8AQJA",
            "statusType": "ACTIVE",
            "statusReason": "RETURN_TO_WORK"
        },
        ...
        {
            "workerStatusId": "00DWS906IMW2JSH8AQK4",
            "statusType": "PENDING_EMPLOYMENT",
            "statusReason": "PENDING_CONTRACT"
        }
    ],
    "links": [
        {
            "rel": "self",
            "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/workerstatuses"
        }
    ]
}

+++++

{
  "content": [
    {
      "workerId": "004WOHNWM9T1I1SFJ1RE",
      "workerType": "EMPLOYEE",
      "sex": "NOT_SPECIFIED",
      "name": {
        "familyName": "Test-11last",
        "givenName": "Test-111"
      },
      "legalId": {
        "legalIdType": "SSN",
        "legalIdValue": "888221111"
      },
      "currentStatus": {
        "workerStatusId": "00ZAJSWSJ0DYTECE004S",
        "statusType": "IN_PROGRESS",
        "statusReason": "PENDING_HIRE",
        "effectiveDate": "2025-04-22T00:00:00Z"
      },
      "links": [
        {
          "rel": "self",
          "href": "https://api.paychex.com/workers/004WOHNWM9T1I1SFJ1RE"
        },
        {
          "rel": "communications",
          "href": "https://api.paychex.com/workers/004WOHNWM9T1I1SFJ1RE/communications"
        }
      ]
    }
  ],
  "links": []
}


    {
      "workerId": "004WOHNWM9T1I1SFJ1RE",
      "workerType": "EMPLOYEE",
      "name": {
        "familyName": "Test-11last",
        "givenName": "Test-111"
      },
      "currentStatus": {
        "workerStatusId": "00ZAJSWSJ0DYTECE004S",
        "statusType": "IN_PROGRESS",
        "statusReason": "PENDING_HIRE",
        "effectiveDate": "2025-04-22T00:00:00Z"
      },
      "links": [
        {
          "rel": "self",
          "href": "https://api.paychex.com/workers/004WOHNWM9T1I1SFJ1RE"
        },
        {
          "rel": "communications",
          "href": "https://api.paychex.com/workers/004WOHNWM9T1I1SFJ1RE/communications"
        }
      ]
    }
    

organization:
{
  "organizationId": "1070061612875206",
  "name": "100 Firefighters",
  "number": "100",
  "level": "Level 1",
  "links": [
    {
      "rel": "self",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061612875206"
    },
    {
      "rel": "parent",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061553681100"
    }
  ]
},
{
  "organizationId": "1070061553681100",
  "name": "Company",
  "links": [
    {
      "rel": "self",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061553681100"
    },
    {
      "rel": "child",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061612875206"
    },
    {
      "rel": "child",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061619221214"
    },
    {
      "rel": "child",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061612875212"
    },
    {
      "rel": "child",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061620089800"
    },
    {
      "rel": "child",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061612875209"
    }
  ]
},
{
  "organizationId": "1070061619221214",
  "name": "200 Administrative Office",
  "number": "200",
  "level": "Level 1",
  "links": [
    {
      "rel": "self",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061619221214"
    },
    {
      "rel": "parent",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061553681100"
    }
  ]
},
{
  "organizationId": "1070061612875212",
  "name": "400 Shop",
  "number": "400",
  "level": "Level 1",
  "links": [
    {
      "rel": "self",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061612875212"
    },
    {
      "rel": "parent",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061553681100"
    }
  ]
},
{
  "organizationId": "1070061620089800",
  "name": "500 Drivers",
  "number": "500",
  "level": "Level 1",
  "links": [
    {
      "rel": "self",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061620089800"
    },
    {
      "rel": "parent",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061553681100"
    }
  ]
},
{
  "organizationId": "1070061612875209",
  "name": "300 Inspection Svc",
  "number": "300",
  "level": "Level 1",
  "links": [
    {
      "rel": "self",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061612875209"
    },
    {
      "rel": "parent",
      "href": "https://api.paychex.com/companies/004UWBZQLAK1M9E3QGHF/organizations/1070061553681100"
    }
  ]
}

location:
{
  "locationId": "1050089142201735",
  "name": "Colorado",
  "address": {
    "streetLineOne": "757 E 20th Ave Ste 370",
    "city": "Denver",
    "postalCode": "80205",
    "countrySubdivisionCode": "CO",
    "countryCode": "US"
  },
  "movedIn": "2023-08-18T00:00:00Z"
},
{
  "locationId": "1060039934748789",
  "name": "Working Location",
  "address": {
    "streetLineOne": "171 Hedrick Creek Ave",
    "city": "Drain",
    "postalCode": "97435",
    "countrySubdivisionCode": "OR",
    "countryCode": "US"
  },
  "movedIn": "2025-04-10T00:00:00Z"
},
{
  "locationId": "1070061682362150",
  "name": "Mailing",
  "address": {
    "streetLineOne": "PO Box 50370",
    "city": "Eugene",
    "postalCode": "97405",
    "countrySubdivisionCode": "OR",
    "countryCode": "US"
  }
}

"""

'''
class PaychexAPI:
    client_id = settings.PAYCHEX_CLIENT_ID
    client_secret = settings.PAYCHEX_CLIENT_SECRET
    base_url = settings.PAYCHEX_BASE_URL

    headers = {}
    access_token = None
    # access_token = "eyJraWQiOiJvaWRjLXByb2QtMTcxODY1MjAyNSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI3NjE0MThjMS04ZjczLTRhYTctYmRiNC00MzE3ZGQ1MDk1ZmEiLCJhdWQiOiJhcGkucGF5Y2hleC5jb20iLCJodHRwOi8vcGF5eC5jb20vc3ViIjoicGF5eHw3NjE0MThjMS04ZjczLTRhYTctYmRiNC00MzE3ZGQ1MDk1ZmEiLCJhenAiOiI3NjE0MThjMS04ZjczLTRhYTctYmRiNC00MzE3ZGQ1MDk1ZmEiLCJjb25zdW1lckluZGljYXRvciI6InBhciIsInNjb3BlIjoiYXBpLWRlbGVnYXRpb24gZXh0LWFwaSByZWFkOmNvbXBhbnlfcGVvcGxlIHdyaXRlOmNvbXBhbnlfcGVvcGxlIiwiaXNzIjoiaHR0cHM6Ly9vaWRjLnBheWNoZXguY29tIiwiZGF0YWNlbnRlciI6ImhkYyIsImV4cCI6MTczODExNjQ3OCwiaWF0IjoxNzM4MTEyODc4LCJqdGkiOiIzZjhkYzUzMy1kZTI3LTQxYjEtOGUxMC0zZjY1YjlkNWQwNGMifQ.TTlcKSZAmmDdg8G1A8y-mc4UIGwgJ2GLsjo2wWrhGix_LAGe465cZ_PQlgUFJTBcmo_7pe7via1HLckaEmaIPpriNP_nluxZ9cgJL5EebCH9bXZTlsJ703Z4Q7aaX4OR0y6BO546NUh7GQp5b0rEvCGvDk2RCy4S3dhgTD8CX-QNpdfdvHZ5Cx9Qztw3NZDIDqJkptujeXFX84evbOuw5rcinSKxTpll534w6lMAmXDv0DxVsQmvIBDFSJueufzVpY3ZXpbeFeQeGTeuruwOU7BSPUDN3euJyIJz7AuiOnkwMa_Z_K3ld9_MN4Ae1LA5FyHURBkAqZkswe96nXpmmw"

    def authenticate(self):
        """Get an OAuth2 token to access the API."""
        # Validate configuration
        if not all([self.client_id, self.client_secret, self.base_url]):
            raise ValueError("Missing required configuration for Paychex API.")

        # Check cached token
        token = cache.get('access_token')
        if token:
            self.access_token = token
            self.create_headers()
            return

        # Prepare request
        url = f"{self.base_url}/auth/oauth/v2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()  # Raise exception for HTTP errors

            # Parse response
            token_data = response.json()
            # print(token_data)
            self.access_token = token_data.get("access_token", None)
            expires_in = token_data.get("expires_in", None)

            if not self.access_token or not expires_in:
                raise ValueError("No access token found in response.")

            # Set token in cache with proper timeout
            cache.set('access_token', self.access_token, timeout=expires_in)
            self.create_headers()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to authenticate with Paychex API: {e}")

    def create_headers(self):
        # print("token:", self.access_token)
        self.headers['Authorization'] = f"Bearer {self.access_token}"
        self.headers['Content-Type'] = "application/json"

    def get_companies(self):
        url = f"{self.base_url}/companies"
        response = requests.get(url, headers=self.headers)
        # response.raise_for_status()
        return response.json()

    def get_company(self, company_id):
        url = f"{self.base_url}/companies/{company_id}"
        response = requests.get(url, headers=self.headers)
        # response.raise_for_status()
        return response.json()

    def get_company_calculationbases(self, company_id):
        url = f"{self.base_url}/companies/{company_id}/calculationbases"
        response = requests.get(url, headers=self.headers)
        # response.raise_for_status()
        return response.json()

    def get_company_contacttypes(self, company_id):
        url = f"{self.base_url}/companies/{company_id}/contacttypes"
        response = requests.get(url, headers=self.headers)
        # response.raise_for_status()
        return response.json()

    def get_company_customfields(self, company_id):
        url = f"{self.base_url}/companies/{company_id}/customfields"
        response = requests.get(url, headers=self.headers)
        # response.raise_for_status()
        return response.json()

    def get_company_customfield(self, company_id, custom_field_id):
        url = f"{self.base_url}/companies/{company_id}/customfields/ {custom_field_id}"
        response = requests.get(url, headers=self.headers)
        # response.raise_for_status()
        return response.json()

    def get_company_organizations(self, company_id):
        url = f"{self.base_url}/companies/{company_id}/organizations"
        response = requests.get(url, headers=self.headers)
        # response.raise_for_status()
        return response.json()

    def get_company_locations(self, company_id):
        url = f"{self.base_url}/companies/{company_id}/locations"
        response = requests.get(url, headers=self.headers)
        # response.raise_for_status()
        return response.json()

    def get_company_workers(
            self,
            company_id,
            givenname=None,
            familyname=None,
            legallastfour=None,
            employeeid=None,
            from_date=None,
            to_date=None,
            locationid=None,
            offset=None,
            limit=None
    ):
        """
        Получение списка работников компании через Paychex API.
        :param company_id: ID компании (обязательный параметр).
        :param givenname: Имя работника.
        :param familyname: Фамилия работника.
        :param legallastfour: Последние 4 цифры налогового ID.
        :param employeeid: ID работника.
        :param from_date: Дата начала периода поиска (ISO 8601).
        :param to_date: Дата окончания периода поиска (ISO 8601).
        :param locationid: ID локации.
        :param offset: Смещение для постраничного отображения.
        :param limit: Лимит на количество записей.
        :return: JSON с данными о работниках компании.
        """
        params = {
            "company_id": company_id,
            "givenname": givenname,
            "familyname": familyname,
            "legallastfour": legallastfour,
            "employeeid": employeeid,
            "from": from_date,
            "to": to_date,
            "locationid": locationid,
            "offset": offset,
            "limit": limit
        }

        params = {key: value for key, value in params.items() if value is not None}
        url = f"{self.base_url}/companies/{company_id}/workers"
        response = requests.get(url, headers=self.headers, params=params)
        # response.raise_for_status()
        return response.json()

    def get_worker(self, worker_id):
        url = f"{self.base_url}/workers/{worker_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def get_worker_communications(self, worker_id):
        url = f"{self.base_url}/workers/{worker_id}/communications"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def get_worker_statuses(self, company_id):
        """
        Получение списка статусов работников компании через Paychex API.
        :param company_id: ID компании (обязательный параметр).
        :return: JSON с данными о статусах работников компании.
        """
        url = f"{self.base_url}/companies/{company_id}/workerstatuses"
        response = requests.get(url, headers=self.headers)
        # response.raise_for_status()
        return response.json()

    def get_worker_status(self, company_id, status_id):
        url = f"{self.base_url}/companies/{company_id}/workerstatuses/{status_id}"
        response = requests.get(url, headers=self.headers)
        # response.raise_for_status()
        return response.json()

    def add_in_progress_worker(self, company_id, worker_data):
        """
        Добавление работника в статусе "In Progress" через Paychex API.
        :param company_id: ID компании (обязательный параметр).
        :param worker_data: Данные о работнике в формате JSON.
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/companies/{company_id}/workers"
        response = requests.post(url, headers=self.headers, json=worker_data)

        # import http.client as http_client
        # http_client.HTTPConnection.debuglevel = 2
        # print("Response headers:")
        # for k, v in response.headers.items():
        #     print(f"{k}: {v}")
        # print("Response body:")
        # print(response.text)

        return response.json()

    def get_company_jobs(self, company_id, asof = None):
        url = f"{self.base_url}/companies/{company_id}/jobs"
        params = {}
        if asof:
            params["asof"] = asof
        response = requests.get(url, headers=self.headers, params=params)
        # response.raise_for_status()
        return response.json()

    def get_companies_checks(self, company_id, pay_period_id, offset=0, limit=0, filter_by_user_id=False):
        """
        Получение списка чеков компании.
        :param company_id: ID компании (обязательный параметр).
        :param pay_period_id: ID периода оплаты (обязательный параметр).
        :param offset: Смещение для постраничного отображения (необязательный параметр, по умолчанию 0).
        :param limit: Лимит на количество записей (необязательный параметр, по умолчанию 0).
        :param filter_by_user_id: Фильтрация по ID пользователя (необязательный параметр, по умолчанию False).
        :return: JSON с данными о чеках компании.
        """
        url = f"{self.base_url}/companies/{company_id}/checks"
        params = {
            "payperiodid": pay_period_id,
            "offset": offset,
            "limit": limit,
            "filterbyuserid": str(filter_by_user_id).lower(),  # API ожидает boolean как строку (true/false)
        }
        response = requests.get(url, headers=self.headers, params=params)
        # response.raise_for_status()
        return response.json()

    def add_company_check(self, company_id, check_data):
        """
        Добавление чека для работника через Paychex API.
        :param company_id: ID компании (обязательный параметр).
        :param check_data: Данные о чеке в формате JSON.
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/companies/{company_id}/checks"
        response = requests.post(url, headers=self.headers, json=check_data)
        # response.raise_for_status()
        return response.json()

    def get_company_pay_components(self, company_id, **params):
        """
        Получение списка компонентов оплаты компании через Paychex API.
        :param company_id: ID компании (обязательный параметр).
        :param params: Дополнительные параметры фильтрации:
            - effecttopay: Тип эффекта оплаты.
            - asof: Дата для фильтрации (ISO 8601).
            - classificationtype: Категория компонента.
            - name: Имя компонента.
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/companies/{company_id}/paycomponents"
        response = requests.get(url, headers=self.headers, params=params)
        # response.raise_for_status()
        return response.json()

    def get_company_pay_component(self, company_id, paycomponent_id, **params):
        """
        Получение информации о компоненте оплаты компании через Paychex API.
        :param company_id: ID компании (обязательный параметр).
        :param paycomponent_id: ID компонента оплаты (обязательный параметр).
        :param params: Дополнительные параметры фильтрации:
            - asof: Дата для фильтрации (ISO 8601).
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/companies/{company_id}/paycomponents/{paycomponent_id}"
        response = requests.get(url, headers=self.headers, params=params)
        # response.raise_for_status()
        return response.json()


    def get_company_pay_periods(self, company_id, status=None, from_date=None, to_date=None):
        """
        Получить список периодов оплаты для компании.

        :param company_id: str, ID компании
        :param status: list, список статусов (например, ["INITIAL", "PROCESSED"])
        :param from_date: str, начало диапазона дат (YYYY-MM-DD)
        :param to_date: str, конец диапазона дат (YYYY-MM-DD)
        :return: JSON с данными периодов оплаты
        """
        url = f"{self.base_url}/companies/{company_id}/payperiods"
        params = {}

        if status:
            params['status'] = status
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date

        response = requests.get(url, headers=self.headers, params=params)
        # response.raise_for_status()
        return response.json()

    def get_company_pay_period(self, company_id, payperiod_id):
        """
        Получение информации о конкретном периоде оплаты компании через Paychex API.
        :param company_id: ID компании (обязательный параметр).
        :param payperiod_id: ID периода оплаты (обязательный параметр).
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/companies/{company_id}/payperiods/{payperiod_id}"
        response = requests.get(url, headers=self.headers)
        # response.raise_for_status()
        return response.json()


    def get_worker_checks(self, worker_id, **params):
        """
        Получение чеков для конкретного работника через Paychex API.
        :param worker_id: ID работника (обязательный параметр).
        :param params: Дополнительные параметры фильтрации:
            - payperiodid: ID периода оплаты (обязательный параметр).
            - filterbyuserid: Фильтрация по ID пользователя (boolean).
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/workers/{worker_id}/checks"
        response = requests.get(url, headers=self.headers, params=params)
        # response.raise_for_status()
        return response.json()

    def add_worker_check(self, worker_id, check_data):
        """
        Добавление чека для работника через Paychex API.
        :param worker_id: ID работника (обязательный параметр).
        :param check_data: Данные чека в формате JSON.
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/workers/{worker_id}/checks"
        response = requests.post(url, headers=self.headers, json=check_data)
        # response.raise_for_status()
        return response.json()


    def get_worker_check(self, worker_id, paycheck_id):
        """
        Получение информации о конкретном чеке работника через Paychex API.
        :param worker_id: ID работника (обязательный параметр).
        :param paycheck_id: ID чека (обязательный параметр).
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/workers/{worker_id}/checks/{paycheck_id}"
        response = requests.get(url, headers=self.headers)
        # response.raise_for_status()
        return response.json()


    def delete_worker_check(self, worker_id, paycheck_id):
        """
        Удаление чека работника через Paychex API.
        :param worker_id: ID работника (обязательный параметр).
        :param paycheck_id: ID чека (обязательный параметр).
        :return: None, если запрос успешен.
        """
        url = f"{self.base_url}/workers/{worker_id}/checks/{paycheck_id}"
        response = requests.delete(url, headers=self.headers)
        # response.raise_for_status()
        return response.status_code


    def delete_checks_by_payperiod_and_user(self, payperiod_id, deletebyuserid):
        """
        Удаление чеков по периоду оплаты и ID пользователя через Paychex API.
        :param payperiod_id: ID периода оплаты (обязательный параметр).
        :param deletebyuserid: Удаление по ID пользователя (обязательный параметр).
        :return: None, если запрос успешен.
        """
        url = f"{self.base_url}/checks"
        params = {"payperiodid": payperiod_id, "deletebyuserid": deletebyuserid}
        response = requests.delete(url, headers=self.headers, params=params)
        # response.raise_for_status()
        return response.status_code


    def add_pay_component_to_check(self, check_id, component_data):
        """
        Добавление компонента оплаты в чек через Paychex API.
        :param check_id: ID чека (обязательный параметр).
        :param component_data: Данные компонента оплаты в формате JSON.
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/checks/{check_id}/checkcomponents"
        response = requests.post(url, headers=self.headers, json=component_data)
        # response.raise_for_status()
        return response.json()


    def delete_pay_component_from_check(self, check_id, check_component_id):
        """
        Удаление компонента оплаты из чека через Paychex API.
        :param check_id: ID чека (обязательный параметр).
        :param check_component_id: ID компонента оплаты (обязательный параметр).
        :return: None, если запрос успешен.
        """
        url = f"{self.base_url}/checks/{check_id}/checkcomponents/{check_component_id}"
        response = requests.delete(url, headers=self.headers)
        # response.raise_for_status()
        return response.status_code


    def update_pay_component_in_check(self, check_id, check_component_id, component_data):
        """
        Обновление компонента оплаты в чеке через Paychex API.
        :param check_id: ID чека (обязательный параметр).
        :param check_component_id: ID компонента оплаты (обязательный параметр).
        :param component_data: Данные компонента оплаты в формате JSON.
        :return: JSON с ответом API.
        """
        url = f"{self.base_url}/checks/{check_id}/checkcomponents/{check_component_id}"
        response = requests.patch(url, headers=self.headers, json=component_data)
        # response.raise_for_status()
        return response.json()
'''
