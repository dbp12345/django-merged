from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Note


class EvernotePwaViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="evernote-pwa-user",
            password="test-pass-123",
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("evernote_pwa:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_logged_in_user_can_create_local_note(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("evernote_pwa:note_create"),
            {
                "title": "First local note",
                "content": "Offline-friendly content",
                "notebook": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        note = Note.objects.get(title="First local note")
        self.assertEqual(note.source, Note.SOURCE_LOCAL)
        self.assertFalse(note.needs_push)
