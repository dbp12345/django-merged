from company.models import Employees
from privser.models import Custom_Fields, Request_To_Privser


class PrivserService:
    key_mapping = {
        "contactName": "contact_name",
        "firstName": "first_name",
        "lastName": "last_name",
        "dateOfBirth": "date_of_birth",
    }
    inverted_key_mapping = {value: key for key, value in key_mapping.items()}

    def get_custom_fields_from_db(self):
        return Custom_Fields.objects.select_related("exchange_property").values(
            "privser_id",
            "privser_name",
            "exchange_property__property_name",
            "main_field",
            # "date_time_format",
            "exchange_property__visibility",
        )

    # update Custom_Fields in db from Privser
    def update_custom_fields_in_db(self):
        from privser.services.PrivserAPI2Service import PrivserAPI2Service
        custom_fields_dict = PrivserAPI2Service().get_custom_fields()

        for custom_field in custom_fields_dict.get("customFields"):
            obj, created = Custom_Fields.objects.get_or_create(
                privser_id=custom_field.get("id"),
                # privser_name=custom_field.get("name"),
            )

            # obj.privser_id = custom_field.get("id")
            obj.privser_name = custom_field.get("name")
            obj.privser_fieldKey = custom_field.get("fieldKey")
            obj.privser_placeholder = custom_field.get("placeholder")
            obj.privser_dataType = custom_field.get("dataType")
            obj.save()

    def get_contacts_in_progres(self):
        return Employees.objects.filter(status_code=Employees.StatusCode.IN_PROGRESS)

    "Not used anywhere yet"
    # def get_in_progress_fields_from_contacts_and_update_privser_db(self, contacts_in_progres):
    #     for contacts_i in contacts_in_progres:
    #         request_to_privser = self.create_request_to_privser_from_contact(contacts_i)
    #         self.handle_request_to_privser(request_to_privser)

    def create_request_to_privser_from_contact(self, contact):
        request_to_privser = Request_To_Privser.objects.create(
            contacts=contact,
            changed_properties=contact.changed_properties,
            status_code=Request_To_Privser.StatusCode.IN_PROGRESS,
            errors=None
        )

        contact.changed_properties = {}
        contact.status_code = Employees.StatusCode.COMPLETED
        contact.save()

        return request_to_privser


    @staticmethod
    def get_all_fields_from_contact_response(contact_response):
        fields_arr = {}
        response = contact_response
        try:
            contact_response = contact_response.get("contact")
            contact_response.pop("contactName", None)  # just delete as unnecessary
            contact_response.pop("emailLowerCase", None)  # just delete as unnecessary
            contact_response.pop("fullNameLowerCase", None)  # just delete as unnecessary
            contact_response.pop("lastNameLowerCase", None)  # just delete as unnecessary
            contact_response.pop("firstNameLowerCase", None)  # just delete as unnecessary
            custom_field = contact_response.pop("customFields")
        except Exception as e:
            print("response", response)
            raise Exception(response) from e

        for key, value in contact_response.items():
            if isinstance(value, str):
                fields_arr[key] = ''.join(c if ord(c) <= 0xFFFF else '?' for c in value)
            else:
                fields_arr[key] = value

        for item_cf in custom_field:
            cf_value = item_cf.get("value")
            if isinstance(cf_value, str):
                fields_arr[item_cf.get("id")] = ''.join(c if ord(c) <= 0xFFFF else '?' for c in cf_value)
            else:
                fields_arr[item_cf.get("id")] = cf_value

        return fields_arr

    @staticmethod
    def update_keys_by_mapping(data):
        updated_dict = {}
        for key, value in data.items():
            new_key = PrivserService.key_mapping.get(key, key)
            updated_dict[new_key] = value
        return updated_dict

    @staticmethod
    def update_keys_by_mapping_inverted(data):
        updated_dict = {}
        for key, value in data.items():
            new_key = PrivserService.inverted_key_mapping.get(key, key)
            updated_dict[new_key] = value
        return updated_dict

    @staticmethod
    def all_notes_to_str_from_res(api_response):
        notes = api_response.get("notes", [])
        note_text = ""
        for note in notes:
            body = note.get("body")
            if body:
                note_text += body + "\n"
        return note_text.strip()

    @staticmethod
    def all_notes_to_list_from_res(api_response):
        notes = api_response.get("notes", [])
        note_list = []
        for note in notes:
            body = note.get("body")
            if body:
                note_list.append(body)
        return note_list

    @staticmethod
    def all_notes_ids_from_res(api_response):
        notes = api_response.get("notes", [])
        ids = []
        for note in notes:
            ids.append(note.get("id"))
        return ids