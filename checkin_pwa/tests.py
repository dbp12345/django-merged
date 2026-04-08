from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class CheckinPwaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="staff-checkin",
            password="test-pass-123",
            is_staff=True,
        )
        self.client.force_login(self.user)

    def test_checkin_page_renders_in_migration_mode(self):
        response = self.client.get(reverse("checkin_pwa:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Migration status:")
        self.assertContains(response, "database writes are intentionally disabled")

    def test_scan_is_blocked_until_mapping_is_configured(self):
        response = self.client.post(reverse("checkin_pwa:scan"), {"contact_id": "123"})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["success"], False)
