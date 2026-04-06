from datetime import timedelta

from django.db import models
from django.db.models import Q
from django.utils.html import format_html
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
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


class Equipment_group(models.Model):
    name = models.CharField(max_length=255)
    # dispatch = models.ForeignKey(
    #     Dispatch,
    #     on_delete=models.SET_NULL,
    #     related_name="equipment_group_entries",
    #     blank=True,
    #     null=True,
    # )
    status = models.CharField(
        "Status",
        max_length=25,
        choices=Status.choices,
        blank=True,
        null=True,
    )
    needs_maintenance = models.BooleanField("Needs maintenance", default=False)
    notes = models.TextField("Notes", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "Equipment group"
        verbose_name_plural = "Equipment groups"

    def __str__(self):
        return self.name or "-"


class Dispatch(models.Model):
    crew = models.ForeignKey(
        "company.FireCrew",
        on_delete=models.SET_NULL,
        related_name="dispatch_entries",
        blank=True,
        null=True,
    )
    crew_archived = models.ForeignKey(
        "company.FireCrew",
        on_delete=models.SET_NULL,
        related_name="dispatch_archived_entries",
        blank=True,
        null=True,
        verbose_name="Crew (archived)",
    )
    fire = models.ForeignKey(
        "company.Fire",
        on_delete=models.SET_NULL,
        related_name="dispatch_entries",
        blank=True,
        null=True,
    )
    contract = models.ForeignKey(
        "dispatch.Contracts",
        on_delete=models.SET_NULL,
        related_name="dispatch_entries",
        null=True,
        blank=True,
    )
    # equipment_group = models.ForeignKey(
    #     Equipment_group,
    #     on_delete=models.SET_NULL,
    #     related_name="dispatch_entries",
    #     blank=True,
    #     null=True
    # )
    equipment_group = models.ManyToManyField(
        "dispatch.Equipment_group",
        related_name="dispatch_entries",
        blank=True,
    )
    manifest = models.FileField(upload_to=model_directory_path, blank=True, null=True)
    resource_order = models.FileField(
        upload_to=model_directory_path, blank=True, null=True
    )
    ec_number = models.CharField("E/C Number", max_length=100, blank=True, null=True)
    status = models.CharField(
        "Status",
        max_length=25,
        choices=Status.choices,
        blank=True,
        null=True,
    )
    needs_maintenance = models.BooleanField("Needs maintenance", default=False)
    notes = models.TextField("Notes", blank=True, null=True)
    company = models.CharField(
        max_length=25,
        choices=Company.choices,
        blank=True,
        null=True,
        editable=True,
        verbose_name="Company",
    )
    camp_location = models.CharField(
        "Camp location", max_length=255, blank=True, null=True
    )
    working_location = models.CharField(
        "Working location", max_length=255, blank=True, null=True
    )
    first_operational_period = models.DateField(
        "First operational period", blank=True, null=True
    )
    fourteenth_operational_period = models.DateField(
        "14th operational period", blank=True, null=True
    )

    payroll_run = models.FileField(
        "Payroll Run", upload_to=model_directory_path, blank=True, null=True
    )
    payroll_ready = models.FileField(
        "Payroll Ready", upload_to=model_directory_path, blank=True, null=True
    )
    status_finance = models.CharField(
        "Status",
        max_length=25,
        choices=StatusFinance.choices,
        blank=True,
        null=True,
    )

    company_rel = models.ForeignKey(
        "company.Company",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="dispatch_entries",
        verbose_name="Company",
    )

    notes_finance = models.TextField("Notes", blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def manifest_preview(self):
        if self.manifest:
            return format_html(
                '<a href="{}" target="_blank">document</a>', self.manifest.url
            )
        return ""

    def resource_order_preview(self):
        if self.resource_order:
            return format_html(
                '<a href="{}" target="_blank">document</a>', self.resource_order.url
            )
        return ""

    class Meta:
        verbose_name = "Dispatch"
        verbose_name_plural = "Dispatches"
        indexes = [
            models.Index(fields=["crew", "status", "updated_at"]),
            models.Index(fields=["crew", "updated_at"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["crew"], name="uniq_dispatch_crew"),
            # ADDED: never allow both crew and crew_archived at the same time
            models.CheckConstraint(
                check=~(Q(crew__isnull=False) & Q(crew_archived__isnull=False)),
                name="no_crew_and_archived_together",
            ),
        ]

    @property
    def display_name(self):
        parts = []
        if self.crew and getattr(self.crew, "crew_boss", None):
            surname = self.crew.crew_boss.get_param_value("surname")
            if surname:
                parts.append(str(surname))
        if self.fire:
            if getattr(self.fire, "fire_number", None):
                parts.append(str(self.fire.fire_number))
            if getattr(self.fire, "incident_name", None):
                parts.append(str(self.fire.incident_name))
            if getattr(self.fire, "state", None):
                parts.append(str(self.fire.state))
        return ", ".join(parts) or str(self)

    def __str__(self):
        parts = []
        "Last name of Crew Boss, E/C Number, fire name, state"
        if self.crew and self.crew.crew_boss:
            parts.append(str(self.crew.crew_boss.get_param_value("surname")))
        elif self.crew:
            parts.append(str(self.crew))
        if self.ec_number:
            parts.append(str(self.ec_number))
        if self.fire:
            parts.append(str(self.fire.fire_number))
            parts.append(str(self.fire.incident_name))
            parts.append(str(self.fire.state))
        if self.first_operational_period:
            parts.append(
                "-".join(
                    (
                        str(self.first_operational_period.strftime("%m/%d/%Y")),
                        str(self.fourteenth_operational_period.strftime("%m/%d/%Y")),
                    )
                )
            )
        return ", ".join(parts)

    def clean(self):
        super().clean()
        if self.crew_id and self.crew_archived_id:
            raise ValidationError(
                {NON_FIELD_ERRORS: ["Crew and archived crew cannot be set together."]}
            )
            # raise ValidationError("Crew and archived crew cannot be set together.")
            # raise ValidationError({
            #     "crew": "Crew and archived crew cannot be set together.",
            #     "crew_archived": "Crew and archived crew cannot be set together.",
            # })

        # if self.crew_id:
        #     qs = Dispatch.objects.filter(crew_id=self.crew_id)
        #     if self.pk:
        #         qs = qs.exclude(pk=self.pk)
        #     if qs.exists():
        #         # raise ValidationError({NON_FIELD_ERRORS: ["This crew is already used by another Dispatch."]})
        #         # raise ValidationError("This crew is already used by another Dispatch.")
        #         raise ValidationError({
        #             "crew": "This crew is already used by another Dispatch.",
        #         })

    def save(self, *args, **kwargs):
        if self.status == Status.NOT_ON_FIRE and self.crew_id:
            if self.crew_archived_id and self.crew_archived_id != self.crew_id:
                raise ValidationError(
                    "Archived crew already set and differs from current crew."
                )
            self.crew_archived_id = self.crew_id
            self.crew_id = None

        if self.first_operational_period:
            self.fourteenth_operational_period = (
                self.first_operational_period + timedelta(days=13)
            )

        super().save(*args, **kwargs)


class DispatchInvoicesProxy(Dispatch):
    class Meta:
        proxy = True
        verbose_name = "Finance tracking"
        verbose_name_plural = "Finance tracking"


class Nomex(models.Model):
    equipment_group = models.ForeignKey(
        Equipment_group,
        on_delete=models.SET_NULL,
        related_name="nomex_entries",
        blank=True,
        null=True,
    )
    type = models.CharField(
        max_length=50, choices=NOMEXTYPE_CHOICES, blank=True, null=True
    )
    size = models.CharField(max_length=50, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
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
    needs_maintenance = models.BooleanField(
        default=False, verbose_name="Needs maintenance"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nomex"
        verbose_name_plural = "Nomex"

    def __str__(self):
        parts = []
        # if self.type:
        #     parts.append(f"Type: {self.type}")
        # if self.size:
        #     parts.append(f"Size: {self.size}")
        # if self.condition:
        #     parts.append(f"Cond: {self.condition}")
        if self.type:
            parts.append(str(self.type))
        if self.size:
            parts.append(str(self.size))
        if self.condition:
            parts.append(str(self.condition))
        # if self.needs_maintenance:
        #     parts.append("Needs maintenance")
        return ", ".join(parts)


class Saw(models.Model):
    equipment_group = models.ForeignKey(
        Equipment_group,
        on_delete=models.SET_NULL,
        related_name="saws_entries",
        blank=True,
        null=True,
    )
    make = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
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
    needs_maintenance = models.BooleanField(
        default=False, verbose_name="Needs maintenance"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Saw"
        verbose_name_plural = "Saws"

    def __str__(self):
        parts = []
        # if self.model:
        #     parts.append(f"Model: {self.model}")
        # if self.condition:
        #     parts.append(f"Cond: {self.condition}")
        # if self.make:
        #     parts.append(f"Make: {self.make}")
        if self.model:
            parts.append(str(self.model))
        # if self.condition:
        #     parts.append(str(self.condition))
        if self.serial_number:
            parts.append(str(self.serial_number))
        # if self.needs_maintenance:
        #     parts.append("Needs maintenance")
        return ", ".join(parts)


class Radio(models.Model):
    equipment_group = models.ForeignKey(
        Equipment_group,
        on_delete=models.SET_NULL,
        related_name="radio_entries",
        blank=True,
        null=True,
    )
    make = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
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
    needs_maintenance = models.BooleanField(
        default=False, verbose_name="Needs maintenance"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Radio"
        verbose_name_plural = "Radios"

    def __str__(self):
        parts = []
        # if self.model:
        #     parts.append(f"Model: {self.model}")
        # if self.serial_number:
        #     parts.append(f"S/N: {self.serial_number}")
        # if self.condition:
        #     parts.append(f"Cond: {self.condition}")
        # if self.make:
        #     parts.append(f"Make: {self.make}")
        if self.model:
            parts.append(str(self.model))
        if self.serial_number:
            parts.append(str(self.serial_number))
        if self.condition:
            parts.append(str(self.condition))
        if self.make:
            parts.append(str(self.make))
        # if self.needs_maintenance:
        #     parts.append("Needs maintenance")
        return ", ".join(parts)


class Phone(models.Model):
    equipment_group = models.ForeignKey(
        Equipment_group,
        on_delete=models.SET_NULL,
        related_name="phone_entries",
        blank=True,
        null=True,
    )
    make = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    imei = models.CharField(max_length=100, blank=True, null=True)
    number = models.CharField(max_length=25, blank=True, null=True)
    pin = models.CharField(max_length=25, blank=True, null=True)
    os = models.CharField(max_length=50, choices=OS_CHOICES, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
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
    needs_maintenance = models.BooleanField(
        default=False, verbose_name="Needs maintenance"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Phone"
        verbose_name_plural = "Phones"

    def __str__(self):
        parts = []
        # if self.name:
        #     parts.append(f"Name: {self.name}")
        # if self.model:
        #     parts.append(f"Model: {self.model}")
        # if self.os:
        #     parts.append(f"OS: {self.os}")
        # if self.condition:
        #     parts.append(f"Cond: {self.condition}")
        # if self.make:
        #     parts.append(f"Make: {self.make}")
        if self.name:
            parts.append(str(self.name))
        if self.model:
            parts.append(str(self.model))
        if self.os:
            parts.append(str(self.os))
        if self.condition:
            parts.append(str(self.condition))
        if self.make:
            parts.append(str(self.make))
        # if self.needs_maintenance:
        #     parts.append("Needs maintenance")
        return ", ".join(parts)


class Truck(models.Model):
    equipment_group = models.ForeignKey(
        Equipment_group,
        on_delete=models.SET_NULL,
        related_name="truck_entries",
        blank=True,
        null=True,
    )
    key = models.SmallIntegerField("Tr#", default=None, blank=True, null=True)
    make = models.CharField("Make", max_length=100, blank=True, null=True)
    model = models.CharField("Model", max_length=100, blank=True, null=True)
    license_plate = models.CharField(
        "License plate", max_length=50, blank=True, null=True
    )
    serial_number = models.CharField(
        "Serial number", max_length=100, blank=True, null=True
    )
    owner = models.CharField(
        "Owner", max_length=50, choices=OWNER_CHOICES, blank=True, null=True
    )
    year = models.IntegerField("Year", blank=True, null=True)
    milage = models.IntegerField("Milage", blank=True, null=True)
    passengers = models.IntegerField("Passengers", blank=True, null=True)

    picture_front = models.ImageField(
        "Picture front", upload_to=model_directory_path, blank=True, null=True
    )
    picture_rear = models.ImageField(
        "Picture rear", upload_to=model_directory_path, blank=True, null=True
    )
    picture_driver_side = models.ImageField(
        "Picture driver side", upload_to=model_directory_path, blank=True, null=True
    )
    picture_passenger_side = models.ImageField(
        "Picture passenger side", upload_to=model_directory_path, blank=True, null=True
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

    status = models.CharField(
        "Status",
        max_length=25,
        choices=Status.choices,
        blank=True,
        null=True,
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
    notes = models.TextField("Notes", blank=True, null=True)

    qr_code = models.ImageField(
        "QR Code", upload_to=model_directory_path, blank=True, null=True
    )

    updated_at = models.DateTimeField("Updated at", auto_now=True)

    def picture_front_preview(self):
        if self.picture_front:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 80px;" />',
                self.picture_front.url,
            )
        return ""

    def picture_rear_preview(self):
        if self.picture_rear:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 80px;" />',
                self.picture_rear.url,
            )
        return ""

    def picture_driver_side_preview(self):
        if self.picture_driver_side:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 80px;" />',
                self.picture_driver_side.url,
            )
        return ""

    def picture_passenger_side_preview(self):
        if self.picture_passenger_side:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 80px;" />',
                self.picture_passenger_side.url,
            )
        return ""

    def qr_code_preview(self):
        if self.qr_code:
            return format_html(
                '<img src="{}" style="max-height: 80px; max-width: 80px;" />',
                self.qr_code.url,
            )
        return ""

    class Meta:
        verbose_name = "Truck"
        verbose_name_plural = "Trucks"

    def __str__(self):
        parts = []
        if self.vin_number:
            parts.append(str(self.vin_number))
        if self.license_plate:
            parts.append(str(self.license_plate))
        if self.model:
            parts.append(str(self.model))
        if self.year:
            parts.append(str(self.year))
        if self.make:
            parts.append(str(self.make))
        # if self.needs_maintenance:
        #     parts.append("Needs maintenance")
        return ", ".join(parts)
