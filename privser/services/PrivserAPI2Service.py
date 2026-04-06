# https://highlevel.stoplight.io/docs/integrations
# https://marketplace.gohighlevel.com/docs/
import http.client
import json
import os
import mimetypes

from django.conf import settings

from core.exceptions import StopTask
from synchronization.models import Sync_Delivery_Logs


class PrivserAPI2Service:
    api_url = settings.PRIVSER_API2_URL
    api_key = settings.PRIVSER_API2_KEY
    location_id = settings.PRIVSER_LOCATION_ID

    def _get_headers(self):
        headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Version': "2021-07-28",
            "Content-Type": "application/json",
            'Accept': "application/json"
        }
        return headers

    def _get_conn(self):
        return http.client.HTTPSConnection(self.api_url)

    def _get_data_from_res(self, res):
        # Headers: [
        #     ('Date', 'Sat, 15 Feb 2025 01:07:48 GMT'),
        #     ('Content-Type', 'application/json; charset=utf-8'),
        #     ('Content-Length', '48'),
        #     ('Connection', 'keep-alive'),
        #     ('x-powered-by', 'Express'),
        #     ('access-control-allow-origin', '*'),
        #     ('x-ratelimit-limit-daily', '200000'), # дневной лимит
        #     ('x-ratelimit-daily-remaining', '0'), # оставшееся количество запросов за день
        #     ('x-ratelimit-daily-reset', '2888000'),
        #     ('x-ratelimit-max', '100'), # максимальный лимит запросов за указанный временной интервал
        #     ('x-ratelimit-remaining', '100'), # оставшееся количество запросов в текущем временном интервале
        #     ('x-ratelimit-interval-milliseconds', '10000'), # временной интервал для пакетных запросов
        #     ('etag', 'W/"30-MT1EemshNaBCNuOTdizV+uy+mgQ"'),
        #     ('vary', 'Accept-Encoding'),
        #     ('x-envoy-upstream-service-time', '6'),
        #     ('strict-transport-security', 'max-age=31536000'),
        #     ('CF-Cache-Status', 'DYNAMIC'),
        #     ('Server', 'cloudflare'),
        #     ('CF-RAY', '91216734fac68e62-PDX')
        # ]
        status = res.status
        headers = {k.lower(): v for k, v in res.getheaders()}  # CHANGED: case-insensitive
        raw = res.read()
        txt = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw or "")
        try:
            data = json.loads(txt) if txt else {}
        except json.JSONDecodeError:
            data = {"raw": txt}  # CHANGED: preserve non-JSON payload

        # CHANGED: handle 429 explicitly
        if status == 429:
            retry_after = headers.get("retry-after")
            daily_remaining = headers.get("x-ratelimit-daily-remaining")
            interval_remaining = headers.get("x-ratelimit-remaining")
            raise Exception(
                f"Rate limit (429). retry_after={retry_after}, "
                f"daily_remaining={daily_remaining}, interval_remaining={interval_remaining}, "
                f"headers={dict(res.getheaders())}, data={data}"
            )

        daily_remaining = headers.get("x-ratelimit-daily-remaining")
        if daily_remaining is not None:
            try:
                if int(daily_remaining) <= 0:
                    raise Exception(
                        f"Rate limit daily_remaining=0. headers={dict(res.getheaders())}, data={data}"
                    )
            except ValueError:
                pass  # CHANGED: ignore malformed value

        # CHANGED: bubble up non-2xx/204 errors with context
        # if not (200 <= status < 300 or status == 204):
        #     raise Exception(f"HTTP {status}: {data}")

        return data

    def get_contacts_by_id(self, contact_id):
        conn = self._get_conn()
        conn.request("GET", f"/contacts/{contact_id}", headers=self._get_headers())
        return self._get_data_from_res(conn.getresponse())

    def search_contacts(self, query=None, page_limit=1):
        # query = {"searchAfter": [1736471515514, "VU1SPQwBqbfa1z9MyaDl"]}
        # query = {
        #     "filters": [
        #         {
        #             "field": "email",
        #             "operator": "eq",
        #             "value": "test10@automation.com"
        #         }
        #     ]
        # }
        # query = {
        #     "filters": [
        #         {
        #             "field": "dateUpdated",
        #             "operator": "range",
        #             "value": {
        #                 "gt": "2025-02-21T00:00:00.000Z",
        #                 # "lt": "2025-02-21T00:00:00.000Z"
        #             }
        #         }
        #     ]
        # }
        query_main = {
            "locationId": self.location_id,
            "pageLimit": page_limit
        }
        if query is not None:
            query_main.update(query)

        conn = self._get_conn()
        payload = json.dumps(query_main)
        conn.request("POST", "/contacts/search", payload, headers=self._get_headers())
        return self._get_data_from_res(conn.getresponse())

    def get_locations(self):
        conn = self._get_conn()
        conn.request("GET", "/locations", headers=self._get_headers())
        return self._get_data_from_res(conn.getresponse())

    def get_duplicate_contact(self):
        conn = self._get_conn()
        conn.request("GET", f"/contacts/search/duplicate?locationId={self.location_id}&email=test10@automation.com", headers=self._get_headers())
        return self._get_data_from_res(conn.getresponse())

    def get_custom_fields(self):
        conn = self._get_conn()
        model = "contact"  # [all, contact, opportunity]
        conn.request("GET", f"/locations/{self.location_id}/customFields?model={model}", headers=self._get_headers())
        return self._get_data_from_res(conn.getresponse())

    def update_contacts_fields(self, contact_id, main_fields=None, custom_fields_list=None):
        # # TO-DO Мы не будем обновлять пока данные
        # from core.exceptions import StopTask
        # from synchronization.models import Sync_Delivery_Logs
        # raise StopTask("Update logic disabled", status_code=Sync_Delivery_Logs.StatusCode.CANCELED.value)

        conn = self._get_conn()
        payload = main_fields
        data = {
            "customFields": custom_fields_list
        }
        payload.update(data)

        conn.request("PUT", f"/contacts/{contact_id}", json.dumps(payload), headers=self._get_headers())
        res = self._get_data_from_res(conn.getresponse())
        return res

    def create_contact(self, email, main_fields=None, custom_fields_list=None):
        conn = self._get_conn()
        payload = {
                      "email": email,
                      "locationId": self.location_id,
                  } | (main_fields or {})
        data = {
            "customFields": custom_fields_list
        }
        payload.update(data)
        conn.request("POST", "/contacts/", body=json.dumps(payload), headers=self._get_headers())
        return self._get_data_from_res(conn.getresponse())

    @staticmethod
    def check_uploaded_custom_field_with(custom_fields_list, response_privser, raise_on_mismatch=False):
        def _s(v):
            return "" if v is None else str(v).strip()

        sent = {str(f["id"]): _s(f.get("field_value")) for f in custom_fields_list}
        received = {str(f["id"]): _s(f.get("value")) for f in response_privser.get("contact", {}).get("customFields", [])}

        diff = {k: v for k, v in sent.items() if received.get(k) != v}

        if diff:
            if raise_on_mismatch:
                raise StopTask(f"Fields not updated correctly: {diff}",
                               status_code=Sync_Delivery_Logs.StatusCode.PROCESSING_ERROR.value)
            else:
                print("❌ Не обновились поля:", diff)
        return diff

    def upload_custom_field_file(self, contact_id: str, field_id: str, file_field):
        if file_field:
            file_path = file_field.path
            file_name = os.path.basename(file_path)

            content_type, encoding = mimetypes.guess_type(file_path)
            content_type = content_type or None

            with open(file_path, "rb") as f:
                files = {
                    field_id: (file_name, f, content_type)
                }

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Version": "2021-07-28"
                }
                params = {
                    "contactId": contact_id,
                    "locationId": self.location_id
                }

                import requests
                response = requests.post(
                    "https://services.leadconnectorhq.com/forms/upload-custom-files",
                    headers=headers,
                    params=params,
                    files=files
                )

                response.raise_for_status()
                return response.json()
        else:
            return None
            # Пока не придумал как удалять картинки удалённо. Потом подумаю..
            # sync_custom_fields_privser_dict = [{
            #     "id": field_id,
            #     "key": "Photo: Driver Front Corner",
            #     "field_value": False
            # }]
            # print("sync_custom_fields_privser_dict:", sync_custom_fields_privser_dict)
            # self.update_contacts_fields(contact_id, main_fields=[], custom_fields_list=sync_custom_fields_privser_dict)


    def get_contacts_by_email(self, email):
        query = {
            "filters": [
                {
                    "field": "email",
                    "operator": "eq",
                    "value": email
                }
            ]
        }
        data = self.search_contacts(query)

        contacts = data.get("contacts", [])
        total = data.get("total", 0)

        if total == 1 and len(contacts) == 1:
            return {
                "status": "one",
                "contact": contacts
            }
        elif total == 0:
            return {
                "status": "none",
                "contact": None
            }
        else:  # total > 1
            return {
                "status": "multiple",
                "contacts": contacts
            }

    def get_all_notes(self, contact_id):
        conn = self._get_conn()
        conn.request("GET", f"/contacts/{contact_id}/notes", headers=self._get_headers())
        return self._get_data_from_res(conn.getresponse())

    def get_note(self, contact_id, note_id):
        conn = self._get_conn()
        conn.request("GET", f"/contacts/{contact_id}/notes/{note_id}", headers=self._get_headers())
        return self._get_data_from_res(conn.getresponse())

    def create_note(self, contact_id, body):
        conn = self._get_conn()
        payload = {
            "userId": contact_id,
            "body": body
        }
        conn.request("POST", f"/contacts/{contact_id}/notes", json.dumps(payload), headers=self._get_headers())
        return self._get_data_from_res(conn.getresponse())

    def update_note(self, contact_id, note_id, body):
        conn = self._get_conn()
        payload = {
            "userId": "GCs5KuzPqTls7vWclkEV",
            "body": body
        }
        conn.request("PUT", f"/contacts/{contact_id}/notes/{note_id}", json.dumps(payload), headers=self._get_headers())
        return self._get_data_from_res(conn.getresponse())

    def delete_note(self, contact_id, note_id):
        conn = self._get_conn()
        conn.request("DELETE", f"/contacts/{contact_id}/notes/{note_id}", headers=self._get_headers())
        return self._get_data_from_res(conn.getresponse())


"""search_contacts
{
    "contacts": [
        {
            "id": "olV8ESTkIxjTCdPD9peS",
            "phoneLabel": null,
            "country": "UG",
            "address": null,
            "source": null,
            "type": "lead",
            "locationId": "oCupZJEoKndmFk1XDVio",
            "website": null,
            "dnd": true,
            "state": "Test-state",
            "businessName": null,
            "customFields": [
                {
                    "id": "SY1NoC9xu6wrhBweehkY",
                    "value": "2013-01-01T00:00:00.000Z"
                },
                {
                    "id": "04rXHtJ3rctIgAXu39aM",
                    "value": "Test-13"
                },
                {
                    "id": "7uSOnJcfst4XQski7gGU",
                    "value": "13"
                },
            ],
            "tags": [
                "instagram applicant - no privser"
            ],
            "dateAdded": "2024-10-23T00:01:51.634Z",
            "additionalEmails": [],
            "phone": "+18888881234",
            "companyName": null,
            "additionalPhones": [],
            "dateUpdated": "2025-01-09T02:48:53.904Z",
            "city": "PrivCity555",
            "dateOfBirth": 1363132800000,
            "firstNameLowerCase": "test-1",
            "lastNameLowerCase": "test-1",
            "email": "test10@automation.com",
            "assignedTo": null,
            "followers": [],
            "validEmail": null,
            "opportunities": [
                {
                    "pipelineId": "3bkWqh91RmVaZqBdbFuj",
                    "id": "52LlSzhkD96ZlaTkVt3a",
                    "monetaryValue": 0,
                    "pipelineStageId": "9c01ac04-8bd6-4336-a5d2-8eb0e1e4bff1",
                    "status": "open"
                }
            ],
            "postalCode": "Test-pcode555",
            "businessId": null,
            "searchAfter": [
                1729641711634,
                "olV8ESTkIxjTCdPD9peS"
            ]
        }
    ],
    "total": 1,
    "traceId": "d819dffd-a314-4284-b03e-7105273a4333"
}


"""
