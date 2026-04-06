from django.db import models
from core.utils import model_directory_path

NOMEXTYPE_CHOICES = [("Pants", "Pants"), ("Shirt", "Shirt")]

CONDITION_CHOICES = [
    ("New", "New"),
    ("Excellent", "Excellent"),
    ("Good", "Good"),
    ("Usable", "Usable"),
    ("Barely Usable", "Barely Usable"),
    ("Needs Repair", "Needs Repair"),
    ("Not repairable", "Not repairable"),
]

OWNER_CHOICES = [
    ("Enterprise", "Enterprise"),
    ("United", "United"),
    ("Flex", "Flex"),
    ("Fleet", "Fleet"),
    ("Other", "Other"),
    ("owned", "owned"),
    ("leased", "leased"),
    ("rented", "rented"),
    ("personal", "personal"),
]

OS_CHOICES = [
    ("IOS", "IOS"),
    ("Android", "Android"),
]

# Available parameter fields for Equipment
# Used for configuration in EquipmentType.fields_config
# Format: {field_name: display_label}
PARAMETER_FIELDS = {
    "imei": "IMEI",
    "number": "Number",
    "pin": "PIN",
    "os": "OS",
    "key": "Tr#",
    "make": "Make",
    "model": "Model",
    "license_plate": "License plate",
    "owner": "Owner",
    "year": "Year",
    "milage": "Milage",
    "passengers": "Passengers",
    "vin_number": "VIN number",
    "gvwr": "GVWR",
    "color": "Color",
    "fuel_type": "Fuel type",
    "insurance_provider": "Insurance provider",
    "registration_state": "Registration state",
    "number_of_doors": "Number of doors",
    "drive": "Drive",
    "motor": "Motor",
    "nomex_type": "Nomex type",
    "condition": "Condition",
    "status": "Status",
    "size": "Size",
}


class Drive(models.TextChoices):
    TYPE_4x4 = "4x4", "4x4"
    TYPE_2x4 = "2x4", "2x4"
    TYPE_6x6 = "6x6", "6x6"
    TYPE_4x6 = "4x6", "4x6"


class Status(models.TextChoices):
    ON_FIRE = "On Fire", "On Fire"
    NOT_ON_FIRE = "Not On Fire", "Not On Fire"
    SCHEDULED = "Scheduled", "Scheduled"


class StatusFinance(models.TextChoices):
    NEEDS_INVOICE = "Needs invoice", "Needs invoice"
    MULTIPLE_INVOICES = "Multiple invoices", "Multiple invoices"


# TO-DO больше не юзаем. Сделали в бд
class Company(models.TextChoices):
    DUST_BUSTERS_PLUS_LLC = "Dust Busters Plus LLC", "Dust Busters Plus LLC"
    IDAHO_LAND_SERVICES_LLC = "Idaho Land Services LLC", "Idaho Land Services LLC"
    DBP_SOUTH_LLC = "DBP South LLC", "DBP South LLC"
    SOUTHERN_SOLUTIONS_LLC = "Southern Solutions LLC", "Southern Solutions LLC"


class EquipmentType(models.Model):
    """Equipment type with field configuration"""

    name = models.CharField("Type name", max_length=255)
    description = models.TextField("Description", blank=True, null=True)

    # Configuration: which fields to use for this type
    fields_config = models.JSONField(
        "Fields configuration",
        default=list,
        blank=True,
        help_text='List of field names to display for this equipment type. Example: ["power", "rpm", "weight"]',
    )

    class Meta:
        verbose_name = "Equipment Type"
        verbose_name_plural = "Equipment Types"

    def __str__(self):
        return self.name


class Equipment(models.Model):
    """Equipment with all possible parameters"""

    # General fields
    equipment_type = models.ForeignKey(
        EquipmentType,
        on_delete=models.PROTECT,
        verbose_name="Equipment type",
        related_name="equipment",
    )
    equipment_group = models.ManyToManyField(
        "dispatch.Equipment_group",
        related_name="equipment_entries",
        blank=True,
    )
    name = models.CharField("Name", max_length=255)
    serial_number = models.CharField(
        "Serial number", max_length=100, blank=True, null=True
    )
    size = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField("Notes", blank=True, null=True)

    imei = models.CharField(max_length=100, blank=True, null=True)
    number = models.CharField(max_length=25, blank=True, null=True)
    pin = models.CharField(max_length=25, blank=True, null=True)
    os = models.CharField(max_length=50, choices=OS_CHOICES, blank=True, null=True)

    key = models.SmallIntegerField("Tr#", default=None, blank=True, null=True)
    make = models.CharField("Make", max_length=100, blank=True, null=True)
    model = models.CharField("Model", max_length=100, blank=True, null=True)
    license_plate = models.CharField(
        "License plate", max_length=50, blank=True, null=True
    )
    owner = models.CharField(
        "Owner", max_length=50, choices=OWNER_CHOICES, blank=True, null=True
    )
    year = models.IntegerField("Year", blank=True, null=True)
    milage = models.IntegerField("Milage", blank=True, null=True)
    passengers = models.IntegerField("Passengers", blank=True, null=True)

    picture = models.ImageField(
        "Picture", upload_to=model_directory_path, blank=True, null=True
    )

    vin_number = models.CharField("VIN number", max_length=100, blank=True, null=True)
    gvwr = models.CharField("gvwr", max_length=100, blank=True, null=True)
    color = models.CharField("Color", max_length=100, blank=True, null=True)
    fuel_type = models.CharField("Fuel type", max_length=100, blank=True, null=True)

    insurance_expiration_date = models.DateField(
        "Insurance exp date", blank=True, null=True
    )
    registration_expiration_date = models.DateField(
        "Registration exp date", blank=True, null=True
    )
    next_service_date = models.DateField("Next service date", blank=True, null=True)

    insurance_provider = models.CharField(
        "Insurance provider", max_length=100, blank=True, null=True
    )
    registration_state = models.CharField(
        "Registration state", max_length=100, blank=True, null=True
    )

    number_of_doors = models.SmallIntegerField(
        "Number of doors", default=None, blank=True, null=True
    )
    drive = models.CharField(
        max_length=100,
        choices=Drive.choices,
        blank=True,
        null=True,
        verbose_name="Drive",
    )
    motor = models.CharField("Motor", max_length=255, blank=True, null=True)
    dot_inspection_date = models.DateField("Dot Inspection Date", blank=True, null=True)
    dot_inspection_file = models.ImageField(
        "Dot Inspection File", upload_to=model_directory_path, blank=True, null=True
    )
    needs_maintenance = models.BooleanField("Needs maintenance", default=False)

    qr_code = models.ImageField(
        "QR Code", upload_to=model_directory_path, blank=True, null=True
    )

    nomex_type = models.CharField(
        max_length=50, choices=NOMEXTYPE_CHOICES, blank=True, null=True
    )
    condition = models.CharField(
        max_length=50, choices=CONDITION_CHOICES, blank=True, null=True
    )
    status = models.CharField(
        "Status",
        max_length=25,
        choices=Status.choices,
        blank=True,
        null=True,
    )

    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "Equipment"
        verbose_name_plural = "Equipment"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.equipment_type.name})"

    def get_configured_fields(self):
        """Get values of configured fields for this equipment type"""
        if not self.equipment_type.fields_config:
            return {}

        result = {}
        for field_name in self.equipment_type.fields_config:
            if hasattr(self, field_name):
                value = getattr(self, field_name)
                if value is not None:
                    result[field_name] = value
        return result
