from django.db import migrations


DEFAULT_GROUP_SLUG = "us-driver-license-starter"
DEFAULT_TEMPLATE_SLUG = "us-driver-license-front"


def seed_default_driver_license_template(apps, schema_editor):
    IDScanGroup = apps.get_model("id_scanner", "IDScanGroup")
    IDScanTemplate = apps.get_model("id_scanner", "IDScanTemplate")
    IDScanField = apps.get_model("id_scanner", "IDScanField")

    group, _ = IDScanGroup.objects.get_or_create(
        slug=DEFAULT_GROUP_SLUG,
        defaults={
            "name": "US Driver License Starter",
            "description": (
                "Starter pipeline for front-side US driver licenses. "
                "Tune ROI boxes per state or card layout."
            ),
            "grayscale_enabled": True,
            "upscale_enabled": True,
            "deskew_enabled": True,
            "binarize_enabled": True,
            "noise_removal_enabled": True,
            "isolate_roi_enabled": True,
            "optimize_ocr_enabled": True,
            "apply_psm_enabled": True,
            "apply_whitelist_enabled": True,
            "post_process_enabled": True,
            "data_validation_enabled": True,
            "remove_background_enabled": True,
            "level_perspective_enabled": True,
            "scale_factor": "1.80",
            "default_psm": 6,
            "threshold_mode": "adaptive",
        },
    )

    template, _ = IDScanTemplate.objects.get_or_create(
        group=group,
        slug=DEFAULT_TEMPLATE_SLUG,
        defaults={
            "name": "US Driver License Front",
            "document_type": "driver_license",
            "issuer_region": "United States",
            "notes": (
                "Starter ROI map for common US license layouts. "
                "Adjust per issuing state for best accuracy."
            ),
            "target_width": 1000,
            "target_height": 630,
        },
    )

    fields = [
        {
            "key": "full_name",
            "label": "Full Name",
            "field_type": "full_name",
            "roi_left": "0.08",
            "roi_top": "0.19",
            "roi_width": "0.52",
            "roi_height": "0.12",
            "psm": 7,
            "whitelist": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz -'",
            "validation_regex": r"[A-Za-z][A-Za-z ,.'-]+",
            "required": True,
            "order": 10,
        },
        {
            "key": "dob",
            "label": "Date of Birth",
            "field_type": "dob",
            "roi_left": "0.08",
            "roi_top": "0.43",
            "roi_width": "0.24",
            "roi_height": "0.08",
            "psm": 7,
            "whitelist": "0123456789/-",
            "validation_regex": r"\d{2}[/-]\d{2}[/-]\d{4}",
            "expected_length": 8,
            "required": True,
            "order": 20,
        },
        {
            "key": "id_number",
            "label": "ID Number",
            "field_type": "id_number",
            "roi_left": "0.58",
            "roi_top": "0.13",
            "roi_width": "0.28",
            "roi_height": "0.10",
            "psm": 7,
            "whitelist": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            "validation_regex": r"[A-Z0-9]{5,16}",
            "required": True,
            "order": 30,
        },
        {
            "key": "expiry",
            "label": "Expiry",
            "field_type": "expiry",
            "roi_left": "0.58",
            "roi_top": "0.43",
            "roi_width": "0.22",
            "roi_height": "0.08",
            "psm": 7,
            "whitelist": "0123456789/-",
            "validation_regex": r"\d{2}[/-]\d{2}[/-]\d{4}",
            "expected_length": 8,
            "required": False,
            "order": 40,
        },
        {
            "key": "address",
            "label": "Address",
            "field_type": "address",
            "roi_left": "0.08",
            "roi_top": "0.56",
            "roi_width": "0.56",
            "roi_height": "0.16",
            "psm": 6,
            "whitelist": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789#-,. ",
            "validation_regex": "",
            "required": False,
            "order": 50,
        },
    ]

    for field_defaults in fields:
        key = field_defaults["key"]
        IDScanField.objects.get_or_create(
            template=template,
            key=key,
            defaults=field_defaults,
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("id_scanner", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_driver_license_template, noop_reverse),
    ]
