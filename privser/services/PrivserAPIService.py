import requests
from django.conf import settings

privser_url = settings.PRIVSER_URL
api_key = settings.PRIVSER_API_KEY

# https://help.gohighlevel.com/support/solutions/articles/48001060529-highlevel-api
class PrivserAPIService:

    def get_headers(self):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        return headers

    def get_all_contacts(self, query: str = None):
        url = f"{privser_url}contacts/"
        if query:
            url = f"{privser_url}contacts/?{query}"
        response = requests.get(url, headers=self.get_headers())

        if response.status_code == 200:
            return response.json()
        else:
            print("Error:", response.status_code, response.text)

    "Not used anywhere yet"
    def get_contacts_by_query(self, query):
        if not query:
            raise ValueError("The requested search string is empty.")

        params = {
            "query": query,
        }
        response = requests.get(f"{privser_url}contacts/", headers=self.get_headers(), params=params)
        # if response.status_code == 200:
        #     data = response.json()
        #     formatted_response = json.dumps(data, indent=4, ensure_ascii=False)
        #     print("Список контактов:", formatted_response)
        # else:
        #     print("Ошибка:", response.status_code, response.text)
        return response.json()

    "Not used anywhere yet"
    def get_custom_fields(self):
        response = requests.get(f"{privser_url}custom-fields/", headers=self.get_headers())
        return response.json()

    "Not used anywhere yet"
    def get_custom_fields_by_user(self, user_id):
        response = requests.get(f"{privser_url}contacts/{user_id}/customFields", headers=self.get_headers())

        return response.json()

    "Not used anywhere yet"
    def update_contacts_fields(self, user_id, main_fields = None, custom_fields = None):
        data = {
            "customField": custom_fields
        }
        data.update(main_fields)
        response = requests.put(f"{privser_url}contacts/{user_id}", json=data, headers=self.get_headers())
        return response.json()

    "Not used anywhere yet"
    def get_contact_id_from_email(self, email):
        data = self.get_contacts_by_query(email)

        # Check the number of contacts in the received data
        if "contacts" in data and len(data["contacts"]) == 1:
            # If exactly one contact is found, return its ID
            return data["contacts"][0]["id"]
        elif "contacts" not in data or len(data["contacts"]) == 0:
            # If no contacts are found, throw an exception
            raise ValueError("No contact found with this email.")
        else:
            # If more than one contact is found, throw an exception
            raise ValueError("More than one contact found with this email.")

    # def update_contact(self, user_id, properties):
    #
    #     # properties = {
    #     #     "firstName": "test9",
    #     #     "last_name": "Doe",
    #     #     "email": "john.doe@example.com",
    #     #     "phone": "+1234567890"
    #     # }
    #
    #     headers = {
    #         "Authorization": f"Bearer {api_key}",
    #         "Content-Type": "application/json"
    #     }
    #
    #     response = requests.put(f"{privser_url}contacts/{user_id}", headers=headers, data=json.dumps(properties))
    #
    #     if response.status_code == 200:
    #         return True
    #     else:
    #         # print(response.status_code, response.text)
    #         return False





# user_id = "sZmDH4ccGYCrYZiIYDf5"
# user_email = "test9@automation.com"

# data = PrivserAPIService().get_contacts()
# data = PrivserAPIService().update_contact()
# data = PrivserAPIService().get_custom_fields()
# data = PrivserAPIService().get_custom_fields_by_user("vgMeNhfdYnH0tNPHHc8y")
# data = PrivserAPIService().get_contacts_by_query("dmytro.svietnoi@gmail.com")
# data = PrivserAPIService().get_contact_id_from_email("dmytro.svietnoi@gmail.com") #vgMeNhfdYnH0tNPHHc8y


# formatted_response = json.dumps(data, indent=4, ensure_ascii=False)
# print(data)
# print(formatted_response)

# {
#     "id": "yU4iHxul0jvMAgt5DVWL",
#     "value": 1727740800000
# }





#v1 curl -X GET "https://rest.gohighlevel.com/v1/contacts/" -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Imw2VmtBYTFMWjkxcHU0YVpnNXhWIiwiY29tcGFueV9pZCI6ImhTdG5iUThTMUtRb1ZVY3RkS2RvIiwidmVyc2lvbiI6MSwiaWF0IjoxNzA2MjE4MjI0NTQzLCJzdWIiOiJ1c2VyX2lkIn0.URMxzVLUUwrn4jfUzSLlsy3HUQPMTKyZzX65bCyfYO4" -H "Content-Type: application/json"
#v2 curl -X GET "https://rest.gohighlevel.com/v2/accounts/" -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Imw2VmtBYTFMWjkxcHU0YVpnNXhWIiwiY29tcGFueV9pZCI6ImhTdG5iUThTMUtRb1ZVY3RkS2RvIiwidmVyc2lvbiI6MSwiaWF0IjoxNzA2MjE4MjI0NTQzLCJzdWIiOiJ1c2VyX2lkIn0.URMxzVLUUwrn4jfUzSLlsy3HUQPMTKyZzX65bCyfYO4" -H "Content-Type: application/json"


"""
{
    "contacts": [
        {
            "id": "vgMeNhfdYnH0tNPHHc8y",
            "locationId": "oCupZJEoKndmFk1XDVio",
            "contactName": "dmy noi",
            "firstName": "dmytro",
            "lastName": "svoi",
            "companyName": null,
            "email": "dmyail.com",
            "phone": "+15416",
            "dnd": false,
            "type": "lead",
            "source": "Instagram Ideal Avatar Campaign",
            "assignedTo": "8AFoI4Dzfx2A89bbydrU",
            "city": "Spfld",
            "state": "OR",
            "postalCode": null,
            "address1": null,
            "dateAdded": "2024-10-15T15:43:49.368Z",
            "dateUpdated": "2024-12-01T00:30:07.840Z",
            "dateOfBirth": "1982-05-12",
            "tags": [
                "instagram applicant",
                "new hire cold"
            ],
            "country": "US",
            "website": null,
            "timezone": "America/Los_Angeles",
            "lastActivity": 1732565973230,
            "customField": [
                {
                    "id": "8AEHkBsuIi2CU3FtoQEF",
                    "value": "No"
                },
                {
                    "id": "5G3hJDl19cHN5JbxFrkn",
                    "value": [
                        "Yes, I agree to receive SMS messages, human resource department messages, company information, news, appointment reminders, work notices, work requests, training, task requests, task request completions"
                    ]
                },
                {
                    "id": "cgOl1pIhu7ixapY8D118",
                    "value": "Yes"
                },
                {
                    "id": "jt0pWC1iWI2ceKl1Zocr",
                    "value": "No"
                },
                {
                    "id": "8TJEU9VQkm6JGjifyWPK",
                    "value": "OR, C727195"
                },
                {
                    "id": "SY1NoC9xu6wrhBweehkY",
                    "value": 1746489600000
                },
                {
                    "id": "av2V1BswRE3OTEkhgkXl",
                    "value": 1735689600000
                }
            ]
        }
    ],
    "meta": {
        "total": 1,
        "nextPageUrl": "http://rest.gohighlevel.com/v1/contacts/?query=dmytro.svietnoi%40gmail.com&startAfter=1729007029368&startAfterId=vgMeNhfdYnH0tNPHHc8y",
        "startAfterId": "vgMeNhfdYnH0tNPHHc8y",
        "startAfter": 1729007029368,
        "currentPage": 1,
        "nextPage": "",
        "prevPage": null
    }
}
"""