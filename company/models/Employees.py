# https://dbdiagram.io/d/67463e5de9daa85acacf7d52
import os
from enum import Enum

from django.conf import settings
from django.db import models, transaction
from django.db.models import Value
from django.db.models.functions import Coalesce
from django.utils.html import format_html

from core.middleware import get_current_user
from core.utils import model_directory_path, model_directory_path_ava
from exchange.models import Contacts_Prop


class DispatchStatus(Enum):
    ACCEPTED_DISPATCH = ("Accepted Dispatch", "#0000ff24")  # Blue
    ARRIVED = ("Arrived", "#ff6f0057")  # Orange
    AVAILABLE_FOR_DISPATCH = ("Available for Dispatch", "#ffff0024")  # Lemon
    CANCELED_DISPATCH = ("Canceled Dispatch", "#ff000024")  # Red
    CHECKED_IN = ("Checked in", "#00800024")  # Green
    DENIED_DISPATCH = ("Denied Dispatch", "#ff000024")  # Red
    IN_ROUTE = ("In Route", "#fd00fd63")  # Pink
    LEAVING_EARLY_IN_ROUTE = ("Leaving Early In Route", "#8b000024")  # Dark Red
    LEFT_EARLY = ("Left Early", "#8b000024")  # Dark Red
    MISSED_DISPATCH_CALL = ("Missed Dispatch Call", "#ffffff24")  # White
    NEEDS_REVIEW = ("Needs Review", "#ff000024")  # Red
    NOT_ELIGIBLE = ("Not Eligible", "#ff000024")  # Red
    NOT_ON_FIRE = ("Not On Fire", "#a52a2a24")  # Brown
    NOT_WORKING_THIS_SEASON = ("Not Working This Season", "#ff000024")  # Red
    ON_FIRE = ("On Fire", "#80808024")  # Gray
    RESTING = ("Resting", "#a52a2a24")  # Brown
    RNR = ("RnR", "#ffffff24")  # White
    TRANSFERRED_OUT = ("Transferred Out", "#ff000024")  # Red

    @property
    def label(self):
        return self.value[0]

    @property
    def color(self):
        return self.value[1]

    @classmethod
    def get_color_by_label(cls, label):
        for status in cls:
            if status.label == label:
                return status.color
        return ""

    @classmethod
    def get_color_by_name(cls, name):
        for status in cls:
            if status.name == name:
                return status.color
        return ""

    @classmethod
    def get_name_by_label(cls, label):
        for status in cls:
            if status.label == label:
                return status.name
        return None


class EmergencyContactType(Enum):
    ADDRESS = "Address"
    CELL_PHONE = "Cell Phone"
    CITY_STATE = "City, State"
    COMPANY_ADDRESS = "Company Address"
    COMPANY_NAME = "Company Name"
    EMAIL = "Email Address"
    FULL_NAME = "Full Name"
    PHONE_HOME = "Phone Home"
    PHONE_WORK = "Phone Work"
    RELATIONSHIP = "Relationship"


# class InteractionType(Enum):
#     CALLED_ANSWERED = "Called Answered"
#     CALLED_NO_ANSWER = "Called No Answer"
#     CALLED_IN = "Called In"
#     EMAIL_RECEIVED = "Email Received"
#     EMAIL_SENT = "Email Sent"
#     RECEIVED_TEXT = "Received Text"
#     SENT_TEXT = "Sent Text"
#     WHATSAPP_RECEIVED = "WhatsApp Received"
#     WHATSAPP_SENT = "WhatsApp Sent"

INTERACTION_STATUS = [
    ("Called Answered", "Called Answered"),
    ("Called No Answer", "Called No Answer"),
    ("Called In", "Called In"),
    ("Email Received", "Email Received"),
    ("Email Sent", "Email Sent"),
    ("Received Text", "Received Text"),
    ("Sent Text", "Sent Text"),
    ("WhatsApp Received", "WhatsApp Received"),
    ("WhatsApp Sent", "WhatsApp Sent"),
    ("Practice Dispatch Confirmed", "Practice Dispatch Confirmed"),
]


class TaskBookType(Enum):
    CRWB = "CRWB"
    ENGB = "ENGB"
    FFT1 = "FFT1"
    ICT5 = "ICT5"
    SAWYER = "Sawyer"


AVAILABILITY_STATUS = [
    ("Available", "Available"),
    ("Done For Season", "Done For Season"),
    ("D Rated", "D Rated"),
    ("Injured", "Injured"),
    ("Left Early", "Left Early"),
    ("Needs Review", "Needs Review"),
    ("No Response", "No Response"),
    ("Not Currently Available", "Not Currently Available"),
    ("Not Eligible To Work", "Not Eligible To Work"),
    ("Not Interested", "Not Interested"),
    ("Not Working This Year", "Not Working This Year"),
    ("Priority", "Priority"),
    ("Transfer", "Transfer"),
]

MEDICAL_CARD_TYPE = [
    ("DOL", "DOL"),
    ("DOT", "DOT"),
]


# class AvailabilityStatus(Enum):
#     AVAILABLE = "Available"
#     DONE_FOR_SEASON = "Done For Season"
#     D_RATED = "D Rated"
#     INJURED = "Injured"
#     LEFT_EARLY = "Left Early"
#     NEEDS_REVIEW = "Needs Review"
#     NO_RESPONSE = "No Response"
#     NOT_CURRENTLY_AVAILABLE = "Not Currently Available"
#     NOT_ELIGIBLE_TO_WORK = "Not Eligible To Work"
#     NOT_INTERESTED = "Not Interested"
#     NOT_WORKING_THIS_YEAR = "Not Working This Year"
#     PRIORITY = "Priority"
#     TRANSFER = "Transfer"
#
#     @classmethod
#     def get_status_value(cls, value):
#         for status in AvailabilityStatus:
#             if status.name == value:
#                 return status.value
#         return None


class JobTitle(Enum):
    FFT1T = "FFT1T"
    FFT1 = "FFT1"
    FFT2 = "FFT2"
    CRWBT = "CRWBT"
    CRWB = "CRWB"
    ENGBT = "ENGBT"
    ENGB = "ENGB"
    REP = "REP"


class EmployeeType(Enum):
    CREW_BOSS = "Crew Boss"
    ENGINE_BOSS = "Engine Boss"
    INSTRUCTOR = "Instructor"
    NORMAL = "Normal"
    SQUAD_BOSS = "Squad Boss"
    CREW_REP = "Crew Rep"


class Hotline(Enum):
    BLANK = "Blank"
    HOTLINE = "Hotline"
    LINE_CONSTRUCTION = "Line Construction"
    NA = "N/A"


class IdentificationDocumentsType(Enum):
    DL = "Driver's License"
    MEDICAL_CARD = "Medical Card"
    PASSPORT = "Passport"
    SSN = "SSN"


DRAWTYPE_CHOICES = [
    "Cash",
    "Wire",
    "Check",
    "Cash App",
    "Other",
    "QR Cash",
    "Zelle",
]


def get_document_preview(document_field):
    """
    Generate HTML preview for document field.
    Supports images (with thumbnail), PDF (with PDF.js preview), and other files (as link).
    """
    if not document_field:
        return ""
    url = document_field.url
    _, ext = os.path.splitext(url)
    ext = ext.lower()

    if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">'
            '<img src="{}" style="max-width:100px; max-height:100px; object-fit:contain;"/></a>',
            url,
            url,
        )

    if ext == ".pdf":
        return format_html(
            '<div class="pdf-preview-container">'
            '<a class="pdf-preview" href="{}" target="_blank" rel="noopener noreferrer" '
            'style="width:160px; height:120px; border:1px solid #ddd; '
            "border-radius:4px; background:#f5f5f5; display:flex; "
            "align-items:center; justify-content:center; cursor:pointer; "
            'position:relative; overflow:hidden; text-decoration:none;" '
            'title="Click to open PDF in new tab">'
            '<span style="color:#999; font-size:12px;">Loading...</span>'
            "</a>"
            "</div>",
            url,
        )

    return format_html(
        '<a href="{}" target="_blank" rel="noopener noreferrer">open</a>', url
    )


class Employees(models.Model):
    class StatusCode(models.IntegerChoices):
        NEW = 0, "New"
        CANCELED = 19, "Canceled"
        COMPLETED = 5, "Completed"
        IN_PROGRESS = 1, "In Progress"
        ERROR = 400, "Error"

    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=255, unique=True)
    type = models.CharField(
        max_length=50,
        choices=[(type.name, type.value) for type in EmployeeType],
        blank=True,
        null=True,
    )
    # Should be unique, but Exchange has non-unique IDs: unique=True
    contact_id = models.CharField(max_length=255, unique=False)
    last_modified_name = models.CharField(max_length=255, blank=True, null=True)
    last_modified_time = models.DateTimeField()
    datetime_created = models.DateTimeField(blank=True, null=True)
    status_code = models.SmallIntegerField(choices=StatusCode, default=StatusCode.NEW)
    test = models.SmallIntegerField(default=0)
    # first_name = models.CharField(max_length=100, blank=True, null=True)  # given_name
    # middle_name = models.CharField(max_length=100, blank=True, null=True)  # middle_name
    # last_name = models.CharField(max_length=100, blank=True, null=True)  # surname
    # job_title = models.CharField(max_length=100, blank=True, null=True)  # job_title
    # phone = models.CharField(max_length=50, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    fire_crew = models.ForeignKey(
        "FireCrew",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    is_manifested = models.BooleanField(default=False)
    document = models.ImageField(
        upload_to=model_directory_path_ava, blank=True, null=True, verbose_name="Photo"
    )
    document_modified_time = models.DateTimeField(blank=True, null=True)
    created_in_exchange = models.SmallIntegerField(default=0)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee",
    )

    tags = models.ManyToManyField("Tag", blank=True, related_name="tags_employees")

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        # constraints = [
        #     models.UniqueConstraint(fields=["email", "contact_id"], name="unique_email_contact_company")
        # ]
        indexes = [
            models.Index(fields=["is_manifested"]),
            models.Index(fields=["fire_crew"]),
        ]

    def updated_at_readable(self):
        return self.updated_at.strftime("%m-%d-%Y %H:%M:%S")

    # @property
    # def name(self):
    #     if self.last_name and self.first_name:
    #         return f"{self.last_name}, {self.first_name} {self.middle_name or ''}".strip()
    #     return " ".join(filter(None, [self.last_name, self.first_name, self.middle_name]))

    @property
    def get_file_as(self):
        surname = self.get_param_value("surname")
        given_name = self.get_param_value("given_name")
        middle_name = self.get_param_value("middle_name")
        if surname:
            rest = " ".join(part for part in [given_name, middle_name] if part)
            return f"{surname}, {rest}" if rest else surname
        else:
            return " ".join(part for part in [given_name, middle_name] if part)

    @property
    def get_email(self):
        return self.get_param_value("email")

    @property
    def get_job_title(self):
        return self.get_param_value("job_title")

    @property
    def get_phone(self):
        return self.get_param_value("MobilePhone")

    def document_preview(self):
        return get_document_preview(self.document)

    def __str__(self):
        return self.get_file_as or self.get_email or "-"
        # if len(self.email) > 36:
        #     return f"{self.email[:36]}..."
        # return self.email
        # return self.email if self.email is not None else ""

    def save(self, *args, **kwargs):
        # if self.email:
        #     self.email = get_unique_email(
        #         self.email,
        #         exclude_employee_id=self.pk if self.pk else None
        #     )

        old = None
        if self.pk:
            try:
                old = Employees.objects.get(pk=self.pk)
            except Employees.DoesNotExist:
                pass

        fire_crew_changed = old and old.fire_crew_id != self.fire_crew_id

        if fire_crew_changed:
            if self.fire_crew:
                FireCrewHistory.objects.create(
                    employee=self,
                    firecrew=self.fire_crew,
                    action=FireCrewHistory.Action.ADDED,
                )
            if old.fire_crew:
                FireCrewHistory.objects.create(
                    employee=self,
                    firecrew=old.fire_crew,
                    action=FireCrewHistory.Action.REMOVED,
                )

            #     новый метод отправки
            from company.services.EmployeesService import EmployeesService
            from core.tasks import handle_sync_delivery_log_task
            from exchange.models import Contacts_Prop
            from synchronization.models import Sync_Delivery_Logs
            from synchronization.services.SyncDeliveryService import SyncDeliveryService

            param_value = self.fire_crew.name if self.fire_crew else None
            employees_service = EmployeesService()
            employees_service.set_contact(employee_obj=self)

            contacts_prop_obj = Contacts_Prop.objects.get(property_name="Crew")
            employees_service.set_contact_parameters(contacts_prop_obj, param_value)

            modified_by = get_current_user()
            if modified_by:
                modified_by = str(modified_by)
            else:
                modified_by = "automation"
            employees_service.do_update_or_create_contact_parameters(
                modified_by=modified_by
            )
            changed_parameters = employees_service.get_all_changed_parameters_obj()
            old_parameters = employees_service.get_old_parameters_obj()

            sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
                employee=self,
                changed_parameters=changed_parameters,
                old_parameters=old_parameters,
                target_system=Sync_Delivery_Logs.TargetSystemChoices.PRIVSER,
                modified_by=modified_by,
            )
            for sync_delivery_log_id in sync_delivery_log_ids:
                if settings.DEBUG:
                    handle_sync_delivery_log_task.run(sync_delivery_log_id)
                else:
                    transaction.on_commit(
                        lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(
                            sync_id
                        )
                    )
                    # handle_sync_delivery_log_task.delay(sync_delivery_log_id)

            sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
                employee=self,
                changed_parameters=changed_parameters,
                old_parameters=old_parameters,
                target_system=Sync_Delivery_Logs.TargetSystemChoices.EXCHANGE,
                modified_by=modified_by,
            )
            for sync_delivery_log_id in sync_delivery_log_ids:
                if settings.DEBUG:
                    handle_sync_delivery_log_task.run(sync_delivery_log_id)
                else:
                    transaction.on_commit(
                        lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(
                            sync_id
                        )
                    )
                    # handle_sync_delivery_log_task.delay(sync_delivery_log_id)

            from core.tasks import check_possibility_firecrew_task

            if settings.DEBUG:
                check_possibility_firecrew_task.run(employee_id=self.id)
            else:
                transaction.on_commit(
                    lambda employee_id=self.id: check_possibility_firecrew_task.delay(
                        employee_id=employee_id
                    )
                )

        super().save(*args, **kwargs)

    def get_param_value(
        self, property_name: str, property_type=Contacts_Prop.TypeChoices.STRING
    ):
        try:
            # Лень расширять это для всех типов.
            if property_type == Contacts_Prop.TypeChoices.DOCUMENT:
                return (
                    self.employees_parameters_entries.select_related("contacts_prop")
                    .get(contacts_prop__property_name=property_name)
                    .value_file
                )
            elif property_type == Contacts_Prop.TypeChoices.SYSTEM_TIME:
                return (
                    self.employees_parameters_entries.select_related("contacts_prop")
                    .get(contacts_prop__property_name=property_name)
                    .value_date
                )
            else:
                return (
                    self.employees_parameters_entries.select_related("contacts_prop")
                    .get(contacts_prop__property_name=property_name)
                    .value
                )
        except Exception:
            return None

    @classmethod
    def filter_by_param(cls, property_name: str, value: str):
        # Получить всех, у кого параметр "Location" = "Oregon"
        # emps = Employees.filter_by_param("Location", "Oregon")
        return cls.objects.filter(
            employees_parameters_entries__contacts_prop__property_name=property_name,
            employees_parameters_entries__value=value,
        ).distinct()


# def get_unique_email(email: str, contact_id: str, exclude_employee_id: int = None) -> str:
#     base_email = email
#     suffix = 1
#     while True:
#         qs = Employees.objects.filter(email=email, contact_id=contact_id)
#         if exclude_employee_id:
#             qs = qs.exclude(id=exclude_employee_id)
#         if not qs.exists():
#             return email
#         email = f"{base_email}_duplicate_{suffix}"
#         suffix += 1


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self) -> str:
        return self.name


class FireCrew(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    crew_boss = models.ForeignKey(
        Employees,
        on_delete=models.SET_NULL,
        related_name="firecrew_entries",
        blank=True,
        null=True,
    )
    visible = models.BooleanField(default=True)
    group = models.CharField(max_length=50, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "FireCrew"
        verbose_name_plural = "FireCrews"
        indexes = [models.Index(fields=["visible", "group"])]

    def __str__(self):
        return self.name or "-"
        # parts = []
        #
        # if self.name:
        #     parts.append(f"Crew name: {self.name}")
        #
        # return ", ".join(parts) if parts else "FireCrew"


class FireCrewHistory(models.Model):
    class Action(models.TextChoices):
        ADDED = "added", "Added"
        REMOVED = "removed", "Removed"

    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees,
        on_delete=models.SET_NULL,
        related_name="firecrew_history_entries",
        blank=True,
        null=True,
    )
    firecrew = models.ForeignKey(
        FireCrew,
        on_delete=models.SET_NULL,
        null=True,
        related_name="firecrew_history_entries",
    )
    action = models.CharField(max_length=10, choices=Action.choices)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Crew History"
        verbose_name_plural = "Crew History"

    def __str__(self):
        return str(self.modified_by)
        # return f"{self.modified_by or 'Unknown user'} ({self.action})"
        # return self.modified_by or f"History #{self.pk}"


class ContactsExchange(Employees):
    class Meta:
        app_label = "exchange"
        proxy = True
        verbose_name = "Employee params"
        verbose_name_plural = "Employees params"


class EmergencyContact(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="emergency_contact_entries"
    )
    relationship = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        related_name="emergency_contact_entries_as_relationship",
        blank=True,
        null=True,
    )
    type = models.CharField(
        max_length=50,
        choices=[(type.name, type.value) for type in EmergencyContactType],
        default=None,
        blank=True,
        null=True,
    )
    relation_to_you = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Emergency Contact"
        verbose_name_plural = "Emergency Contacts"

    def __str__(self):
        parts = [f"Employee: {self.employee}"]

        if self.relationship:
            parts.append(f"Relationship: {self.relationship}")

        if self.type:
            parts.append(f"Type: {self.type}")

        if self.relation_to_you:
            parts.append(f"Relation: {self.relation_to_you}")

        if self.is_primary:
            parts.append("Primary: Yes")

        return ", ".join(parts)


class MSPA(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="mspa_entries"
    )
    issue_date = models.DateField(blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True)
    MSPA_number = models.CharField(max_length=255, blank=True, null=True)
    # link_to_document = models.URLField(max_length=255, blank=True, null=True)
    pending = models.DateField(blank=True, null=True)
    document = models.FileField(upload_to=model_directory_path, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "MSPA"
        verbose_name_plural = "MSPA"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]

        if self.issue_date:
            parts.append(f"Issue date: {self.issue_date}")

        if self.expiration_date:
            parts.append(f"Expiration date: {self.expiration_date}")

        if self.MSPA_number:
            parts.append(f"MSPA number: {self.MSPA_number}")

        return ", ".join(parts)

    def document_preview(self):
        return get_document_preview(self.document)


class IdentificationDocuments(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        related_name="identification_documents_entries",
    )
    type = models.CharField(
        max_length=50,
        choices=[(type.name, type.value) for type in IdentificationDocumentsType],
        blank=False,
        null=False,
    )
    issue_date = models.DateField(blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True)
    number = models.CharField(max_length=255, blank=True, null=True)
    document = models.FileField(upload_to=model_directory_path, blank=True, null=True)
    endorsement = models.CharField(max_length=255, blank=True, null=True)
    restriction = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Identification Document"
        verbose_name_plural = "Identification Documents"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=["number", "employee"],
        #         condition=~Q(number__in=["", "X", "0", "None", "none"]) & Q(number__isnull=False),
        #         name="unique_number_per_employee"
        #     )
        # ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]
        if self.type:
            parts.append(f"Type: {self.type}")
        if self.issue_date:
            parts.append(f"Issue date: {self.issue_date}")
        if self.expiration_date:
            parts.append(f"Expiration date: {self.expiration_date}")
        if self.number:
            parts.append(f"Number: {self.number}")
        if self.endorsement:
            parts.append(f"Endorsement: {self.endorsement}")
        if self.restriction:
            parts.append(f"Restriction: {self.restriction}")
        return ", ".join(parts)

    def document_preview(self):
        return get_document_preview(self.document)


class DriverLicense(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        related_name="dl_documents_entries",
    )
    issue_date = models.DateField(blank=True, null=True, verbose_name="Issue Date")
    expiration_date = models.DateField(
        blank=True, null=True, verbose_name="Expiration Date"
    )
    number = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="State, Number"
    )
    endorsement = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Endorsements"
    )
    restriction = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Restrictions"
    )
    front_of_id = models.FileField(
        upload_to=model_directory_path,
        blank=True,
        null=True,
        verbose_name="Front of ID",
    )
    back_of_id = models.FileField(
        upload_to=model_directory_path, blank=True, null=True, verbose_name="Back of ID"
    )
    id_2_front = models.FileField(
        upload_to=model_directory_path, blank=True, null=True, verbose_name="ID 2 Front"
    )
    id_2_back = models.FileField(
        upload_to=model_directory_path, blank=True, null=True, verbose_name="ID 2 Back"
    )
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Driver License"
        verbose_name_plural = "Driver License"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]
        if self.issue_date:
            parts.append(f"Issue date: {self.issue_date}")
        if self.expiration_date:
            parts.append(f"Expiration date: {self.expiration_date}")
        if self.number:
            parts.append(f"Number: {self.number}")
        if self.endorsement:
            parts.append(f"Endorsement: {self.endorsement}")
        if self.restriction:
            parts.append(f"Restriction: {self.restriction}")
        return ", ".join(parts)

    def front_of_id_preview(self):
        return get_document_preview(self.front_of_id)

    def back_of_id_preview(self):
        return get_document_preview(self.back_of_id)

    def id_2_front_preview(self):
        return get_document_preview(self.id_2_front)

    def id_2_back_preview(self):
        return get_document_preview(self.id_2_back)


class MedicalCard(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        related_name="medical_card_entries",
    )
    issue_date = models.DateField(blank=True, null=True, verbose_name="Issue Date")
    expiration_date = models.DateField(
        blank=True, null=True, verbose_name="Expiration Date"
    )
    type = models.CharField(
        max_length=50,
        choices=MEDICAL_CARD_TYPE,
        default="",
        blank=True,
        null=True,
        verbose_name="Type",
        help_text="Type of medical card",
    )
    document = models.FileField(upload_to=model_directory_path, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Medical Card"
        verbose_name_plural = "Medical Card"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]
        if self.issue_date:
            parts.append(f"Issue date: {self.issue_date}")
        if self.expiration_date:
            parts.append(f"Expiration date: {self.expiration_date}")
        if self.type:
            parts.append(f"Type: {self.type}")
        return ", ".join(parts)

    def document_preview(self):
        return get_document_preview(self.document)


class Passport(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        related_name="passport_entries",
    )
    issue_date = models.DateField(blank=True, null=True, verbose_name="Issue Date")
    expiration_date = models.DateField(
        blank=True, null=True, verbose_name="Expiration Date"
    )
    number = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Number"
    )
    document = models.FileField(upload_to=model_directory_path, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Passport"
        verbose_name_plural = "Passport"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]
        if self.issue_date:
            parts.append(f"Issue date: {self.issue_date}")
        if self.expiration_date:
            parts.append(f"Expiration date: {self.expiration_date}")
        if self.number:
            parts.append(f"Number: {self.number}")
        return ", ".join(parts)

    def document_preview(self):
        return get_document_preview(self.document)


class SocialSecurityNumber(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        related_name="ssn_entries",
    )
    expiration_date = models.DateField(
        blank=True, null=True, verbose_name="Expiration Date"
    )
    number = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Number"
    )
    document = models.FileField(upload_to=model_directory_path, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Social Security Number"
        verbose_name_plural = "Social Security Number"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]
        if self.number:
            parts.append(f"Number: {self.number}")
        return ", ".join(parts)

    def document_preview(self):
        return get_document_preview(self.document)


class DispatchingStatus(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="dispatching_status_entries"
    )
    date = models.DateTimeField(blank=True, null=True)
    time = models.CharField(
        max_length=50, blank=True, null=True
    )  # We take this from the names of the columns in the Exchange (Just some additional information)
    # office_personnel = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, default="")
    positive_interaction = models.BooleanField(default=False)
    dispatch_status = models.CharField(
        max_length=50,
        choices=[(status.name, status.label) for status in DispatchStatus],
        default=None,
        blank=True,
        null=True,
    )
    dispatch_category = models.CharField(max_length=50, blank=True, default="")
    ETA = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def set_dispatch_status_by_value(self, value):
        self.dispatch_status = self.get_dispatch_status_key(value)

    @classmethod
    def get_dispatch_status_key(cls, value):
        for status in DispatchStatus:
            if status.label == value:
                return status.name
        return None

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Dispatching status"
        verbose_name_plural = "Dispatching statuses"
        indexes = [models.Index(fields=["employee", "updated_at"])]

    def __str__(self):
        return f"{self.employee} - {self.dispatch_status}"
        # parts = [
        #     f"Employee: {self.employee}"
        # ]
        #
        # if self.date:
        #     parts.append(f"Date: {self.date}")
        #
        # if self.dispatch_status:
        #     parts.append(f"Status: {self.dispatch_status}")
        #
        # if self.dispatch_call_status:
        #     parts.append(f"Call status: {self.dispatch_call_status}")
        #
        # if self.dispatch_category:
        #     parts.append(f"Category: {self.dispatch_category}")
        #
        # if self.ETA:
        #     parts.append(f"ETA: {self.ETA}")
        #
        # if self.location:
        #     parts.append(f"Location: {self.location}")
        #
        # if self.positive_interaction:
        #     parts.append("Positive interaction: Yes")
        #
        # return ", ".join(parts)


class CompanyManifest(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="company_manifest_entries"
    )
    # We take this from the names of the columns in the Exchange (Just some additional information)
    # year = models.IntegerField(blank=True, null=True)
    date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Manifest"
        verbose_name_plural = "Manifests"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]

        if self.date:
            parts.append(f"Date: {self.date}")

        return ", ".join(parts)


class DrugTest(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="drug_test_entries"
    )
    date = models.DateField(blank=True, null=True)
    result = models.CharField(max_length=50, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Drug Test"
        verbose_name_plural = "Drug Tests"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]

        if self.date:
            parts.append(f"Date: {self.date}")

        if self.result:
            parts.append(f"Result: {self.result}")

        return ", ".join(parts)


class NomexCheckOut(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="nomex_checkout_entries"
    )
    date = models.DateField(blank=True, null=True)
    pants_serial_number = models.CharField(max_length=255, blank=True, null=True)
    shirt_serial_number = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Nomex CheckOut"
        verbose_name_plural = "Nomex CheckOut"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]

        if self.date:
            parts.append(f"Date: {self.date}")

        if self.pants_serial_number:
            parts.append(f"Pants serial: {self.pants_serial_number}")

        if self.shirt_serial_number:
            parts.append(f"Shirt serial: {self.shirt_serial_number}")

        return ", ".join(parts)


class NomexCheckIn(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="nomex_checkin_entries"
    )
    date = models.DateField(blank=True, null=True)
    pants_serial_number = models.CharField(max_length=255, blank=True, null=True)
    shirt_serial_number = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Nomex CheckIn"
        verbose_name_plural = "Nomex CheckIn"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]

        if self.date:
            parts.append(f"Date: {self.date}")

        if self.pants_serial_number:
            parts.append(f"Pants serial: {self.pants_serial_number}")

        if self.shirt_serial_number:
            parts.append(f"Shirt serial: {self.shirt_serial_number}")

        return ", ".join(parts)


class EmploymentPacket(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="employment_packet_entries"
    )
    packet_name = models.CharField(max_length=255, blank=True, null=True)
    date_sent = models.DateField(blank=True, null=True)
    date_signed = models.DateField(blank=True, null=True)
    # link_to_document = models.URLField(max_length=255, blank=True, null=True)
    document = models.FileField(upload_to=model_directory_path, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Employment Packet"
        verbose_name_plural = "Employment Packets"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]

        if self.packet_name:
            parts.append(f"Packet name: {self.packet_name}")

        if self.date_sent:
            parts.append(f"Date sent: {self.date_sent}")

        if self.date_signed:
            parts.append(f"Date signed: {self.date_signed}")

        return ", ".join(parts)

    def document_preview(self):
        return get_document_preview(self.document)


class IQCCard(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="IQC_card_entries"
    )
    position = models.CharField(max_length=255, blank=True, null=True)
    pack_test = models.CharField(max_length=255, blank=True, null=True)
    document = models.FileField(upload_to=model_directory_path, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "IQC Card"
        verbose_name_plural = "IQC Cards"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]

        if self.position:
            parts.append(f"Position: {self.position}")

        if self.pack_test:
            parts.append(f"Pack test: {self.pack_test}")

        if self.date:
            parts.append(f"Date: {self.date}")

        return ", ".join(parts)

    def document_preview(self):
        return get_document_preview(self.document)


class Interaction(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="interaction_entries"
    )
    type_of_interaction = models.CharField(
        max_length=50, choices=INTERACTION_STATUS, default=None, blank=True, null=True
    )
    date = models.DateTimeField(blank=True, null=True)
    # office_personnel = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, default="")
    negative_interaction = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Interaction"
        verbose_name_plural = "Interactions"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]

        if self.type_of_interaction:
            parts.append(f"Type: {self.type_of_interaction}")

        if self.date:
            parts.append(f"Date: {self.date}")

        if self.negative_interaction:
            parts.append("Negative: Yes")

        return ", ".join(parts)


class TaskBook(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="task_book_entries"
    )
    type_of_taskbook = models.CharField(
        max_length=50,
        choices=[(type.name, type.value) for type in TaskBookType],
        default=None,
        blank=True,
        null=True,
    )
    initiated_date = models.DateField(blank=True, null=True)
    completed_date = models.DateField(blank=True, null=True)
    updated_date = models.DateField(blank=True, null=True)
    final_evaluator = models.CharField(max_length=255, blank=True, null=True)
    # link_to_document = models.URLField(max_length=255, blank=True, null=True)
    document = models.FileField(upload_to=model_directory_path, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "TaskBook"
        verbose_name_plural = "TaskBooks"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]

        if self.type_of_taskbook:
            parts.append(f"Type: {self.type_of_taskbook}")

        if self.initiated_date:
            parts.append(f"Initiated: {self.initiated_date}")

        if self.completed_date:
            parts.append(f"Completed: {self.completed_date}")

        if self.updated_date:
            parts.append(f"Updated: {self.updated_date}")

        if self.final_evaluator:
            parts.append(f"Final evaluator: {self.final_evaluator}")

        return ", ".join(parts)

    def document_preview(self):
        return get_document_preview(self.document)


class Availability(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="availability_entries"
    )
    availability_status = models.CharField(
        max_length=50, choices=AVAILABILITY_STATUS, default=None, blank=True, null=True
    )
    date_of_change = models.DateField(blank=True, null=True)
    date_of_expected_future_change = models.DateField(blank=True, null=True)
    # office_personnel = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, default="")
    travel_time = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    location_state = models.CharField(
        "Current Location, State", max_length=255, blank=True, default=""
    )
    location_city = models.CharField(
        "Current Location, City", max_length=255, blank=True, default=""
    )
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Availability"
        verbose_name_plural = "Availability"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]

        if self.availability_status:
            parts.append(f"Status: {self.availability_status}")

        # if self.date_of_change:
        #     parts.append(f"Date of change: {self.date_of_change}")

        if self.date_of_expected_future_change:
            parts.append(f"Expected change date: {self.date_of_expected_future_change}")

        return ", ".join(parts)


class CurrentAssigned(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="current_assigned_entries"
    )
    date = models.DateField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Current Assigned"
        verbose_name_plural = "Current Assigned"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]

        if self.date:
            parts.append(f"Date: {self.date}")

        return ", ".join(parts)


class Notes(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="notes_entries"
    )
    body = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        if len(self.body) > 100:
            return f"{self.body[:100]}..."
        return self.body or "-"


class TrainingType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Class type"
        verbose_name_plural = "Class type"

    def __str__(self):
        return self.name or "-"


class Course(models.Model):
    id = models.AutoField(primary_key=True)
    # training_type = models.ForeignKey(
    #     TrainingType,
    #     on_delete=models.CASCADE,
    #     related_name="training_type_entries",
    #     unique=True
    # )
    training_type = models.OneToOneField(
        TrainingType,
        on_delete=models.CASCADE,
        related_name="training_type_entries",
    )
    # name = models.CharField(max_length=50, blank=False, null=False, unique=True)
    inperson_required = models.BooleanField(default=False)
    governing_body = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return self.training_type.name or "-"

    # def __str__(self):
    #     parts = []
    #
    #     if self.training_type.name:
    #         parts.append(f"Type: {self.training_type.name}")
    #
    #     parts.append(f"In-person required: {'Yes' if self.inperson_required else 'No'}")
    #
    #     if self.governing_body:
    #         parts.append(f"Governing body: {self.governing_body}")
    #
    #     return ", ".join(parts)


class TrainingClass(models.Model):
    id = models.AutoField(primary_key=True)
    # employee = models.ForeignKey(
    #     Employees,
    #     on_delete=models.CASCADE,
    #     related_name="training_class_entries_as_employee"
    # )
    instructor = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        related_name="training_class_entries_as_instructor",
        blank=True,
        null=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="training_class_entries",
        blank=True,
        null=True,
    )
    test_score = models.IntegerField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    association = models.CharField("Association", max_length=255, blank=True, null=True)
    document = models.FileField(upload_to=model_directory_path, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        constraints = [
            models.UniqueConstraint(
                fields=["course", "date"], name="unique_course_date"
            )
        ]

    def __str__(self):
        course_name = (
            self.course.training_type.name
            if self.course and self.course.training_type
            else "No Type"
        )
        date_str = self.date.strftime("%m/%d/%Y") if self.date else "No Date"
        return f"{course_name} - {date_str}"
        # return str(self.date.strftime("%m/%d/%Y")) if self.date is not None else ""

        # parts = [
        #     # f"Employee: {self.employee}",
        #     f"Instructor: {self.instructor}" if self.instructor else "Instructor: None"
        # ]
        #
        # if self.course:
        #     parts.append(f"Course: {self.course}")
        #
        # if self.test_score is not None:
        #     parts.append(f"Test score: {self.test_score}")
        #
        # if self.date:
        #     parts.append(f"Date: {self.date}")
        #
        # if self.location:
        #     parts.append(f"Location: {self.location}")
        #
        # return ", ".join(parts)

    def document_preview(self):
        return get_document_preview(self.document)


class Student(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="student_entries"
    )
    training_class = models.ForeignKey(
        TrainingClass,
        on_delete=models.CASCADE,
        related_name="student_entries",
        verbose_name="Class",
    )
    test_score = models.IntegerField("Test score", blank=True, null=True)
    verified = models.DateField("Verified", blank=True, null=True)
    certificate_confirmed = models.DateField(
        "Certificate confirmed", blank=True, null=True
    )
    # link_to_document = models.URLField(max_length=255, blank=True, null=True)
    document = models.FileField(
        "Document", upload_to=model_directory_path, blank=True, null=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        # Этот параметр указывает Django не управлять созданием, удалением и миграциями таблицы.
        # managed = False
        # сохранить старую таблицу и просто изменить приложение, в котором модель отображается
        # db_table = 'old_app_mymodel'
        verbose_name = "Student"
        verbose_name_plural = "Students"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}", f"Training class: {self.training_class}"]

        if self.test_score is not None:
            parts.append(f"Test score: {self.test_score}")

        return ", ".join(parts)

    def document_preview(self):
        return get_document_preview(self.document)


class RateOfPay(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="rate_of_pay_entries"
    )
    base_rate = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    bonus_rate = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    office_rate = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    year = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Rate Of Pay"
        verbose_name_plural = "Rate Of Pay"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]

    def __str__(self):
        parts = [f"Employee: {self.employee}"]

        if self.base_rate is not None:
            parts.append(f"Base rate: {self.base_rate}")

        if self.bonus_rate is not None:
            parts.append(f"Bonus rate: {self.bonus_rate}")

        if self.office_rate is not None:
            parts.append(f"Office rate: {self.office_rate}")

        if self.year:
            parts.append(f"Year temporary: {self.year}")

        return ", ".join(parts)


class Fire(models.Model):
    id = models.AutoField(primary_key=True)
    fire_number = models.CharField(max_length=100, blank=True, null=True)
    incident_name = models.CharField(max_length=100, blank=True, null=True)
    incident_type = models.CharField(max_length=50, blank=True, null=True)
    agency = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=25, blank=True, null=True)
    reliability_leaving = models.IntegerField(blank=True, null=True)
    activity_code = models.CharField(
        "Activity code", max_length=25, blank=True, null=True
    )
    fuel_type = models.CharField("Fuel type", max_length=25, blank=True, null=True)
    fire_size = models.CharField("Fire size", max_length=10, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Fire"
        verbose_name_plural = "Fires"
        constraints = [
            models.UniqueConstraint(
                Coalesce("fire_number", Value("-")),
                Coalesce("incident_name", Value("-")),
                name="uniq_fire_num_name_null_token",
            ),
        ]

    def __str__(self):
        parts = []

        if self.fire_number:
            parts.append(self.fire_number)

        if self.incident_name:
            parts.append(self.incident_name)

        if self.incident_type is not None:
            parts.append(f"Type {self.incident_type}")

        if self.agency:
            parts.append(f"Agency. {self.agency}")

        if self.state:
            parts.append(self.state)

        # if self.reliability_leaving is not None:
        #     parts.append(f"Reliability leaving: {self.reliability_leaving}")

        return ", ".join(parts) if parts else "Fire"


class Crew(models.Model):
    id = models.AutoField(primary_key=True)
    crew_name = models.CharField(
        max_length=255, blank=True, null=True
    )  # Логируем и заполняем из этого crew_boss
    crew_boss = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        related_name="crew_entries",
        blank=True,
        null=True,
    )
    # crew_boss = models.ForeignKey(
    #     Employees,
    #     on_delete=models.CASCADE,
    #     related_name="crew_boss_entries",
    #     blank=True, null=True
    # )
    fire = models.ForeignKey(
        Fire,
        on_delete=models.SET_NULL,
        related_name="crew_entries",
        blank=True,
        null=True,
    )
    dispatch = models.ForeignKey(
        "dispatch.Dispatch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="crew_entries",
    )
    c_number = models.CharField(max_length=100, null=False, blank=False)
    contract = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Crew (history)"
        verbose_name_plural = "Crews (history)"
        constraints = [
            models.UniqueConstraint(
                fields=["fire", "c_number"], name="unique_fire_c_number"
            )
        ]

    def __str__(self):
        parts = []

        if self.fire:
            parts.append(self.fire.fire_number)

        if self.c_number:
            parts.append(self.c_number)

        if self.crew_name:
            parts.append(self.crew_name)

        if self.contract:
            parts.append(self.contract)

        return ", ".join(parts) if parts else "Crew"


class FireRun(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        related_name="fire_run_entries",
        blank=True,
        null=True,
    )
    crwb = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        related_name="fire_run_entries_as_crwb",
        blank=True,
        null=True,
    )
    crew = models.ForeignKey(
        Crew, on_delete=models.CASCADE, related_name="fire_run_entries"
    )
    task_book = models.ForeignKey(
        TaskBook,
        on_delete=models.CASCADE,
        related_name="fire_run_entries",
        blank=True,
        null=True,
    )
    firefighter_name = models.CharField(
        max_length=255, blank=True, null=True
    )  # Логируем и заполняем из этого employee
    CRWB_potential = models.CharField(max_length=255, blank=True, null=True)
    rating = models.CharField("Rating", max_length=10, blank=True, null=True)
    ranking = models.CharField("Ranking", max_length=10, blank=True, null=True)
    professionalism_rating = models.CharField(max_length=10, blank=True, null=True)
    attitude_rating = models.CharField(max_length=10, blank=True, null=True)
    sawyer_rating = models.CharField(max_length=10, blank=True, null=True)
    month_year = models.CharField(max_length=255, blank=True, null=True)
    hotline_shifts = models.IntegerField("Hotline shifts", blank=True, null=True)
    start_date = models.DateField("Incident date", blank=True, null=True)
    job_title = models.CharField(
        max_length=50,
        choices=[(status.name, status.value) for status in JobTitle],
        default=None,
        blank=True,
        null=True,
    )
    # Ли говорил, что нам не надо это поле. Но ХЗ, оставлю пока, потому что там есть инфо из импорта
    total_shift_tickets = models.IntegerField(
        "Total shift tickets", blank=True, null=True
    )
    operational_periods = models.IntegerField("Oper. periods", blank=True, null=True)
    activity_code = models.CharField(
        "Activity code", max_length=25, blank=True, null=True
    )  # move to Fire. Need to remove from here
    fuel_type = models.CharField(
        "Fuel type", max_length=25, blank=True, null=True
    )  # move to Fire. Need to remove from here
    fire_size = models.CharField(
        "Fire size", max_length=10, blank=True, null=True
    )  # move to Fire. Need to remove from here
    eval_hotline = models.CharField(
        "Eval hotline", max_length=10, blank=True, null=True
    )
    hotline_in_remarks = models.BooleanField(
        "Hotline in remarks", blank=True, null=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Fire Run"
        verbose_name_plural = "Fire Run"
        indexes = [
            models.Index(fields=["employee", "updated_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["crew", "employee", "job_title"], name="unique_crew_employee_jt"
            )
        ]

    def __str__(self):
        parts = [
            f"Employee: {self.employee}" if self.employee else "Employee: None",
            f"Crew: {self.crew}",
        ]

        if self.crew.c_number:
            parts.append(f"C number: {self.crew.c_number}")

        if self.CRWB_potential:
            parts.append(f"CRWB potential: {self.CRWB_potential}")

        if self.rating:
            parts.append(f"Rating: {self.rating}")

        if self.ranking:
            parts.append(f"Ranking: {self.ranking}")

        if self.professionalism_rating:
            parts.append(f"Professionalism rating: {self.professionalism_rating}")

        if self.attitude_rating:
            parts.append(f"Attitude rating: {self.attitude_rating}")

        if self.sawyer_rating:
            parts.append(f"Sawyer rating: {self.sawyer_rating}")

        if self.month_year:
            parts.append(f"Month/Year: {self.month_year}")

        if self.hotline_shifts:
            parts.append(f"Hotline shifts: {self.hotline_shifts}")

        return ", ".join(parts)


class CrewTimeReport(models.Model):
    id = models.AutoField(primary_key=True)
    crew = models.ForeignKey(
        Crew,
        on_delete=models.CASCADE,
        related_name="crew_time_report_entries",
        blank=True,
        null=True,
    )
    # link_to_document = models.URLField(max_length=255, blank=True, null=True)
    document = models.FileField(upload_to=model_directory_path, blank=True, null=True)
    hotline_in_remarks = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Crew Time Report"
        verbose_name_plural = "Crew Time Reports"

    def __str__(self):
        parts = [f"Crew: {self.crew}" if self.crew else "Crew: None"]

        if self.hotline_in_remarks:
            parts.append("Hotline in remarks: Yes")

        return ", ".join(parts)

    def document_preview(self):
        return get_document_preview(self.document)


class Evaluation(models.Model):
    id = models.AutoField(primary_key=True)
    crew = models.ForeignKey(
        Crew,
        on_delete=models.CASCADE,
        related_name="evaluation_entries",
        blank=True,
        null=True,
    )
    rated_by = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    hotline = models.CharField(
        max_length=50,
        choices=[(type.name, type.value) for type in Hotline],
        default=None,
        blank=True,
        null=True,
    )
    # link_to_document = models.URLField(max_length=255, blank=True, null=True)
    document = models.FileField(upload_to=model_directory_path, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Evaluation"
        verbose_name_plural = "Evaluations"

    def __str__(self):
        parts = [f"Crew: {self.crew}" if self.crew else "Crew: None"]

        if self.rated_by:
            parts.append(f"Rated by: {self.rated_by}")

        if self.date:
            parts.append(f"Date: {self.date}")

        if self.hotline:
            parts.append(f"Hotline: {self.hotline}")

        return ", ".join(parts)

    def document_preview(self):
        return get_document_preview(self.document)


class DayOnFire(models.Model):
    id = models.AutoField(primary_key=True)
    fire_run = models.ForeignKey(
        FireRun, on_delete=models.CASCADE, related_name="day_on_fire_entries"
    )
    crew_time_report = models.ForeignKey(
        CrewTimeReport,
        on_delete=models.CASCADE,
        related_name="day_on_fire_entries",
        default=None,
        blank=True,
        null=True,
    )
    job_title = models.CharField(
        max_length=50,
        choices=[(status.name, status.value) for status in JobTitle],
        default=None,
        blank=True,
        null=True,
    )
    date = models.DateField(blank=True, null=True)
    clockin1 = models.DateTimeField(blank=True, null=True)
    clockout1 = models.DateTimeField(blank=True, null=True)
    clockin2 = models.DateTimeField(blank=True, null=True)
    clockout2 = models.DateTimeField(blank=True, null=True)
    hours_per_day = models.DecimalField(
        max_digits=4, decimal_places=2, blank=True, null=True
    )
    hotline_in_remarks = models.BooleanField("Hotline in remarks", default=False)
    operational_periods = models.BooleanField("Operational periods", default=False)
    document = models.FileField(upload_to=model_directory_path, blank=True, null=True)
    # job_title = models.CharField(max_length=255, blank=True, null=True)
    # total_shift_tickets = models.IntegerField(blank=True, null=True)
    # operational_periods = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and "modified_by" not in kwargs.get("update_fields", []):
            self.modified_by = str(user)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Day On Fire"
        verbose_name_plural = "Days On Fire"

    def __str__(self):
        parts = [f"FireRun: {self.fire_run}", f"CTR: {self.crew_time_report}"]

        if self.job_title:
            parts.append(f"job_title: {self.job_title}")

        if self.clockin1:
            parts.append(f"clockin1: {self.clockin1}")

        if self.clockout1:
            parts.append(f"clockout1: {self.clockout1}")

        if self.clockin2:
            parts.append(f"clockin2: {self.clockin2}")

        if self.clockout2:
            parts.append(f"clockout2: {self.clockout2}")

        if self.hours_per_day:
            parts.append(f"hours_per_day: {self.hours_per_day}")

        return ", ".join(parts)

    def document_preview(self):
        return get_document_preview(self.document)

    document_preview.short_description = "Document preview"


class Draws(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(
        Employees, on_delete=models.CASCADE, related_name="draws_entries"
    )
    date = models.DateTimeField(blank=True, null=True)
    type = models.CharField(
        max_length=50,
        choices=[(val, val) for val in DRAWTYPE_CHOICES],
        blank=True,
        null=True,
    )
    amount = models.CharField(max_length=50, blank=True, null=True)
    signature = models.CharField(max_length=50, blank=True, null=True)
    payer = models.CharField(max_length=100, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "Draws"
        verbose_name_plural = "Draws"
