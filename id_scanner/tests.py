from __future__ import annotations

import os
import shutil
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import IDScanField, IDScanGroup, IDScanRecord, IDScanTemplate
from .services import ScanDependencyError, _build_tesseract_config


TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff"
    b"\xff?\x00\x05\xfe\x02\xfeA\xf4\x9b\xd1\x00\x00\x00\x00IEND\xaeB`\x82"
)


TEST_MEDIA_ROOT = os.path.join(os.getcwd(), "test_media_id_scanner")
os.makedirs(TEST_MEDIA_ROOT, exist_ok=True)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class IDScannerViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.user = user_model.objects.create_superuser(
            username="scanner-admin",
            email="scanner@example.com",
            password="password123",
        )
        cls.group = IDScanGroup.objects.create(name="Default Group", slug="default-group")
        cls.template = IDScanTemplate.objects.create(
            group=cls.group,
            name="California ID",
            slug="california-id",
        )
        IDScanField.objects.create(
            template=cls.template,
            key="full_name",
            label="Full Name",
            field_type=IDScanField.FIELD_FULL_NAME,
            roi_left=0.10,
            roi_top=0.10,
            roi_width=0.35,
            roi_height=0.12,
            required=True,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = Client()

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("id_scanner:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_scan_submit_requires_image(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("id_scanner:scan_submit"),
            {"group_id": self.group.id, "template_id": self.template.id},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(IDScanRecord.objects.count(), 0)

    def test_scan_submit_returns_processed_payload(self):
        self.client.force_login(self.user)

        def fake_process(record):
            record.status = IDScanRecord.STATUS_SUCCESS
            record.confidence_score = Decimal("96.50")
            record.extracted_data = {
                "full_name": {
                    "label": "Full Name",
                    "value": "Jane Example",
                    "raw_text": "JANE EXAMPLE",
                    "valid": True,
                    "errors": [],
                }
            }
            record.save()
            return record

        upload = SimpleUploadedFile("scan.png", TINY_PNG, content_type="image/png")
        with patch("id_scanner.views.process_record", side_effect=fake_process):
            response = self.client.post(
                reverse("id_scanner:scan_submit"),
                {
                    "group_id": self.group.id,
                    "template_id": self.template.id,
                    "image": upload,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["fields"]["full_name"]["value"], "Jane Example")

    def test_scan_submit_surfaces_dependency_error(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile("scan.png", TINY_PNG, content_type="image/png")
        with patch(
            "id_scanner.views.process_record",
            side_effect=ScanDependencyError("Tesseract OCR is not available."),
        ):
            response = self.client.post(
                reverse("id_scanner:scan_submit"),
                {
                    "group_id": self.group.id,
                    "template_id": self.template.id,
                    "image": upload,
                },
            )

        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload["error"], "Tesseract OCR is not available.")

    def test_scan_submit_surfaces_unexpected_exception_text(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile("scan.png", TINY_PNG, content_type="image/png")
        with patch("id_scanner.views.process_record", side_effect=RuntimeError("simulated boom")):
            response = self.client.post(
                reverse("id_scanner:scan_submit"),
                {
                    "group_id": self.group.id,
                    "template_id": self.template.id,
                    "image": upload,
                },
            )

        self.assertEqual(response.status_code, 500)
        payload = response.json()
        self.assertEqual(payload["error"], "RuntimeError: simulated boom")

    def test_default_driver_license_seed_exists(self):
        group = IDScanGroup.objects.get(slug="us-driver-license-starter")
        template = IDScanTemplate.objects.get(group=group, slug="us-driver-license-front")
        self.assertEqual(template.document_type, IDScanTemplate.DOCUMENT_DRIVER_LICENSE)
        self.assertEqual(template.fields.count(), 5)
        self.assertTrue(template.fields.filter(key="full_name", required=True).exists())

    def test_state_driver_license_templates_seed_exists(self):
        group = IDScanGroup.objects.get(slug="us-driver-license-starter")
        california = IDScanTemplate.objects.get(group=group, slug="us-ca-driver-license-front")
        texas = IDScanTemplate.objects.get(group=group, slug="us-tx-driver-license-front")
        self.assertEqual(california.issuer_region, "California")
        self.assertEqual(texas.issuer_region, "Texas")
        self.assertEqual(california.fields.count(), 5)

    def test_admin_roi_preview_page_loads(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("admin:id_scanner_idscantemplate_roi_preview", args=[self.template.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ROI Preview")
        self.assertContains(response, self.template.name)

    def test_pwa_icon_assets_exist(self):
        base_dir = os.path.join(os.getcwd(), "id_scanner", "static", "id_scanner")
        self.assertTrue(os.path.exists(os.path.join(base_dir, "icon-192.png")))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "icon-512.png")))
        self.assertTrue(os.path.exists(os.path.join(base_dir, "icon-maskable-512.png")))

    def test_tesseract_config_quotes_whitelist_safely(self):
        field = self.template.fields.get(key="full_name")
        field.whitelist = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz -'"
        config = _build_tesseract_config(field, self.group)
        self.assertIn('--psm 6', config)
        self.assertIn('tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz -\'"', config)
