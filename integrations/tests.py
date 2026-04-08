from __future__ import annotations

from datetime import timedelta
from unittest.mock import Mock, patch

from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from .ghl_client import GHLNotConnected, request
from .models import GHLAuth
from .views import ghl_oauth_callback
from .ghl_sync import push_django_to_ghl, disable_sync, enable_sync
from companies.models import Company
from contacts.models import Contact


class GHLOAuthTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("integrations.views.requests.post")
    def test_callback_stores_auth_per_location_without_overwriting_existing_auth(self, mock_post):
        GHLAuth.objects.create(
            access_token="old_access",
            refresh_token="old_refresh",
            expires_at=timezone.now() + timedelta(hours=1),
            location_id="loc_old",
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access",
            "refresh_token": "new_refresh",
            "expires_in": 3600,
            "locationId": "loc_new",
        }
        mock_post.return_value = mock_response

        request_obj = self.factory.get("/oauth/callback/", {"code": "abc123"})
        response = ghl_oauth_callback(request_obj)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(GHLAuth.objects.count(), 2)
        self.assertTrue(GHLAuth.objects.filter(location_id="loc_old").exists())
        self.assertTrue(GHLAuth.objects.filter(location_id="loc_new").exists())

    @patch("integrations.views.requests.post")
    def test_callback_updates_existing_auth_for_same_location(self, mock_post):
        GHLAuth.objects.create(
            access_token="old_access",
            refresh_token="old_refresh",
            expires_at=timezone.now() + timedelta(hours=1),
            location_id="loc_same",
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access",
            "refresh_token": "new_refresh",
            "expires_in": 3600,
            "locationId": "loc_same",
        }
        mock_post.return_value = mock_response

        request_obj = self.factory.get("/oauth/callback/", {"code": "abc123"})
        response = ghl_oauth_callback(request_obj)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(GHLAuth.objects.count(), 1)
        auth = GHLAuth.objects.get(location_id="loc_same")
        self.assertEqual(auth.access_token, "new_access")
        self.assertEqual(auth.refresh_token, "new_refresh")


class GHLClientTests(TestCase):
    @override_settings(GHL_LOCATION_ID="loc_b")
    @patch("integrations.ghl_client.requests.request")
    def test_request_uses_auth_for_configured_location(self, mock_request):
        GHLAuth.objects.create(
            access_token="token_a",
            refresh_token="refresh_a",
            expires_at=timezone.now() + timedelta(hours=1),
            location_id="loc_a",
        )
        GHLAuth.objects.create(
            access_token="token_b",
            refresh_token="refresh_b",
            expires_at=timezone.now() + timedelta(hours=1),
            location_id="loc_b",
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"{}"
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response

        request("POST", "/contacts/search", json={"query": "test@example.com"})

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer token_b")
        self.assertEqual(kwargs["json"]["locationId"], "loc_b")

    def test_request_raises_when_configured_location_has_no_auth(self):
        with self.settings(GHL_LOCATION_ID="loc_missing"):
            with self.assertRaises(GHLNotConnected):
                request("GET", "/contacts")


class GHLSyncModeTests(TestCase):
    @override_settings(GHL_LOCATION_ID="loc_read_only")
    @patch("integrations.ghl_sync.request")
    def test_push_skips_writes_for_read_only_location(self, mock_request):
        GHLAuth.objects.create(
            access_token="token_ro",
            refresh_token="refresh_ro",
            expires_at=timezone.now() + timedelta(hours=1),
            location_id="loc_read_only",
            sync_mode=GHLAuth.SyncMode.READ_ONLY,
        )

        company = Company.objects.create(name="Read Only Co")
        disable_sync()
        try:
            contact = Contact.objects.create(
                company=company,
                role="customer",
                first_name="Read",
                last_name="Only",
                email="readonly@example.com",
                phone="+15550000009",
            )
        finally:
            enable_sync()

        result = push_django_to_ghl(queryset=Contact.objects.filter(pk=contact.pk))

        self.assertEqual(result.skipped, 1)
        mock_request.assert_not_called()
