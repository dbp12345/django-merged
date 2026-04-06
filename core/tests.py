from core.models import Contacts_Prop_Logs
import traceback, json
from django.test import TestCase
from django.urls import reverse

class MyViewTest(TestCase):
    def test_example(self):

        # obj = Contacts_Prop_Logs.objects.create(body="10")
        # obj.save()
        # print("Created object:", obj)
        # self.assertIsNotNone(obj.id)
        #
        #
        # obj = Contacts_Prop_Logs.objects.create(body="10")
        # print("Created object:", obj)
        #
        # # Проверяем, что объект был создан
        # self.assertIsNotNone(obj.id)

        try:

            response = self.client.post(
                reverse("handle_requested_data"),
                data=json.dumps({"email": "test2@automation.com", "customData": {"Last Login LD": "2024-01-02"}}),
                content_type="application/json"
            )
            print(response)

            self.assertEqual(response.status_code, 200)
            # res = edit_field("Test 3", "String", "ttesttt", "test10@automation.com")
            # print(res)

            obj = Contacts_Prop_Logs.objects.last()
            # self.assertEqual(obj.name, "Test object")
            print(f"\nemail: {obj.email}\nstatus_code: {obj.status_code}\nbody: {obj.body}\nupdated_at: {obj.updated_at}\n")

        except Exception:
            traceback.print_exc()


        # self.assertEqual(1 + 1, 2)


    # def setUp(self):
    #     property_name_to_set = ""
    #     property_type_to_set = ""
    #     field_value_to_set = ""
    #     contact_email = ""
    #
    # class SimpleTest(TestCase):
    #     # def setUp(self):
    #     #     # Every tests needs access to the request factory.
    #     #     self.factory = RequestFactory()
    #     #     self.user = User.objects.create_user(
    #     #         username="jacob", email="jacob@…", password="top_secret"
    #     #     )
    #
    # def test_edit_field(self):
    #     print("ttt")
    #     data = {"Test 3": 1230}