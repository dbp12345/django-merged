from django.db import migrations


BASE_GROUP_SLUG = "us-driver-license-starter"
BASE_TEMPLATE_SLUG = "us-driver-license-front"

US_JURISDICTIONS = [
    ("AL", "Alabama"),
    ("AK", "Alaska"),
    ("AZ", "Arizona"),
    ("AR", "Arkansas"),
    ("CA", "California"),
    ("CO", "Colorado"),
    ("CT", "Connecticut"),
    ("DE", "Delaware"),
    ("FL", "Florida"),
    ("GA", "Georgia"),
    ("HI", "Hawaii"),
    ("ID", "Idaho"),
    ("IL", "Illinois"),
    ("IN", "Indiana"),
    ("IA", "Iowa"),
    ("KS", "Kansas"),
    ("KY", "Kentucky"),
    ("LA", "Louisiana"),
    ("ME", "Maine"),
    ("MD", "Maryland"),
    ("MA", "Massachusetts"),
    ("MI", "Michigan"),
    ("MN", "Minnesota"),
    ("MS", "Mississippi"),
    ("MO", "Missouri"),
    ("MT", "Montana"),
    ("NE", "Nebraska"),
    ("NV", "Nevada"),
    ("NH", "New Hampshire"),
    ("NJ", "New Jersey"),
    ("NM", "New Mexico"),
    ("NY", "New York"),
    ("NC", "North Carolina"),
    ("ND", "North Dakota"),
    ("OH", "Ohio"),
    ("OK", "Oklahoma"),
    ("OR", "Oregon"),
    ("PA", "Pennsylvania"),
    ("RI", "Rhode Island"),
    ("SC", "South Carolina"),
    ("SD", "South Dakota"),
    ("TN", "Tennessee"),
    ("TX", "Texas"),
    ("UT", "Utah"),
    ("VT", "Vermont"),
    ("VA", "Virginia"),
    ("WA", "Washington"),
    ("WV", "West Virginia"),
    ("WI", "Wisconsin"),
    ("WY", "Wyoming"),
    ("DC", "District of Columbia"),
]


def seed_us_state_driver_license_templates(apps, schema_editor):
    IDScanGroup = apps.get_model("id_scanner", "IDScanGroup")
    IDScanTemplate = apps.get_model("id_scanner", "IDScanTemplate")
    IDScanField = apps.get_model("id_scanner", "IDScanField")

    try:
        group = IDScanGroup.objects.get(slug=BASE_GROUP_SLUG)
        base_template = IDScanTemplate.objects.get(group=group, slug=BASE_TEMPLATE_SLUG)
    except (IDScanGroup.DoesNotExist, IDScanTemplate.DoesNotExist):
        return

    base_fields = list(base_template.fields.order_by("order", "id"))
    template_defaults = {
        "document_type": base_template.document_type,
        "notes": (
            "Starter state-specific front template cloned from the generic US driver license "
            "layout. Tune ROI boxes and OCR settings for this jurisdiction."
        ),
        "is_active": True,
        "target_width": base_template.target_width,
        "target_height": base_template.target_height,
        "accepted_date_input_formats": base_template.accepted_date_input_formats,
    }

    for code, state_name in US_JURISDICTIONS:
        template, _ = IDScanTemplate.objects.get_or_create(
            group=group,
            slug=f"us-{code.lower()}-driver-license-front",
            defaults={
                **template_defaults,
                "name": f"{state_name} Driver License Front",
                "issuer_region": state_name,
            },
        )

        for field in base_fields:
            IDScanField.objects.get_or_create(
                template=template,
                key=field.key,
                defaults={
                    "label": field.label,
                    "field_type": field.field_type,
                    "roi_left": field.roi_left,
                    "roi_top": field.roi_top,
                    "roi_width": field.roi_width,
                    "roi_height": field.roi_height,
                    "psm": field.psm,
                    "whitelist": field.whitelist,
                    "validation_regex": field.validation_regex,
                    "expected_length": field.expected_length,
                    "required": field.required,
                    "normalize_whitespace": field.normalize_whitespace,
                    "order": field.order,
                },
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("id_scanner", "0002_seed_default_driver_license_template"),
    ]

    operations = [
        migrations.RunPython(seed_us_state_driver_license_templates, noop_reverse),
    ]
