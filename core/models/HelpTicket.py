from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group

from core.utils import model_directory_path

ALLOWED_ATTACHMENT_FIELDS = {
    "employees",
    "firecrew",
    "dispatch",
    "equipment_group",
    "saw",
    "radio",
    "phone",
    "truck",
}
# __Change help ticket status names - task from Lee
# Send = Not started
# Processing = Started
# Completed  = Finished
# Un Resolved = Unable to complete
STATUS_CHOICES = [
    ("send", "Not started"),
    ("processing", "Started"),
    ("completed", "Finished"),
    ("unresolved", "Unable to complete"),
    ("waiting", "Waiting for other tasks"),
]

PRIORITY_LEVEL = [
    ("10", "10 (High)"),
    ("09", "9"),
    ("08", "8"),
    ("07", "7"),
    ("06", "6"),
    ("05", "5 (Middle)"),
    ("04", "4"),
    ("03", "3"),
    ("02", "2"),
    ("01", "1 (Low)"),
    ("-", "-"),
]


class ToolsChoices(models.TextChoices):
    SUPPLIES = "supplies", "Supplies needed"
    TOOLS = "tools", "Tools needed"
    BOTH = "both", "Supplies and tools needed"
    UNKNOWN = "unknown", "Unknown"
    NONE = "none", "No supplies or tools needed"


# Запросы примеры:
#
# Все тикеты, прикреплённые к конкретному Dispatch:
# HelpTicket.objects.filter(dispatch=dispatch_instance)
#
# Все тикеты, прикреплённые к типу Dispatch:
# HelpTicket.objects.filter(dispatch__isnull=False)
#
# Все тикеты, где вообще есть привязка:
# HelpTicket.objects.filter(models.Q(employee__isnull=False) |
# models.Q(firerun__isnull=False) |
# models.Q(dispatch__isnull=False)
class HelpTicket(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField("Title", max_length=255)

    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Parent ticket",
    )

    prerequisite = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dependent_tickets",
        verbose_name="Prerequisite ticket",
    )

    category = models.ForeignKey(
        "core.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="help_ticket",
    )
    body = models.TextField("Ticket", blank=True, null=True)
    note = models.TextField("Note", blank=True, null=True)
    status = models.CharField(
        "Status", max_length=50, choices=STATUS_CHOICES, default="send"
    )
    priority = models.CharField(
        "Priority level", max_length=50, choices=PRIORITY_LEVEL, default="-"
    )
    tools = models.CharField(
        "Supplies/tools",
        max_length=32,
        choices=ToolsChoices.choices,
        blank=True,
        default="",
    )
    document = models.FileField(
        "Document", upload_to=model_directory_path, blank=True, null=True
    )
    date_opened = models.DateTimeField("Date opened", blank=True, null=True)
    date_completed = models.DateTimeField("Date completed", blank=True, null=True)

    created_for = models.ForeignKey(
        "company.Employees",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_for_tickets",
        verbose_name="Created for",
    )
    assigned_to = models.ForeignKey(
        "company.Employees",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_to_tickets",
        verbose_name="Assigned to",
    )
    assigned_to_group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_group_tickets",
        verbose_name="Assigned to group",
    )

    # <-- four target FKs (nullable) -->
    employees = models.ForeignKey(
        "company.Employees",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tickets_as_employees",
    )
    firecrew = models.ForeignKey(
        "company.FireCrew",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tickets_as_firecrew",
    )
    dispatch = models.ForeignKey(
        "dispatch.Dispatch",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tickets_as_dispatch",
    )
    equipment_group = models.ForeignKey(
        "dispatch.Equipment_group",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tickets_as_equipment_group",
    )
    saw = models.ForeignKey(
        "dispatch.Saw",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tickets_as_saw",
    )
    radio = models.ForeignKey(
        "dispatch.Radio",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tickets_as_radio",
    )
    phone = models.ForeignKey(
        "dispatch.Phone",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tickets_as_phone",
    )
    truck = models.ForeignKey(
        "dispatch.Truck",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tickets_as_truck",
    )
    equipment = models.ForeignKey(
        "dispatch.Equipment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tickets_as_equipment",
    )

    created_by = models.ForeignKey(
        "company.Employees",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tickets",
        verbose_name="Created by",
    )
    created_by_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tickets_admin",
        verbose_name="Created by admin",
    )
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["assigned_to_group"]),
            models.Index(fields=["employees"]),
            models.Index(fields=["firecrew"]),
            models.Index(fields=["dispatch"]),
            models.Index(fields=["equipment_group"]),
            models.Index(fields=["saw"]),
            models.Index(fields=["radio"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["truck"]),
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["category"]),
            models.Index(fields=["prerequisite"]),
        ]

    def __str__(self):
        return f"{self.title}"

    def document_preview(self):
        from company.models.Employees import get_document_preview
        return get_document_preview(self.document)

    document_preview.short_description = "Document preview"

    def get_attached(self):
        for name in ALLOWED_ATTACHMENT_FIELDS:
            obj = getattr(self, name)
            if obj is not None:
                return name, obj
        return None, None

    def _has_cycle(self) -> bool:
        """Detect parent cycle."""
        seen = set()
        node = self.parent
        while node:
            if node.pk == self.pk or node.pk in seen:
                return True
            seen.add(node.pk)
            node = node.parent
        return False

    def clean(self):
        targets = ALLOWED_ATTACHMENT_FIELDS
        set_targets = [t for t in targets if getattr(self, t) is not None]
        if len(set_targets) > 1:
            raise ValidationError(
                "Ticket must be attached to at most one object. Found: "
                + ", ".join(set_targets)
            )

        if self.parent_id and self._has_cycle():
            raise ValidationError("Parent relation creates a cycle.")

        # Check prerequisite cycle
        from core.services.HelpTicketPrerequisiteService import check_prerequisite_cycle
        if check_prerequisite_cycle(self):
            raise ValidationError("Prerequisite relation creates a cycle.")

    def save(self, *args, **kwargs):
        self.full_clean()

        # Track old status to detect completion
        old_status = None
        if self.pk:
            try:
                old_instance = HelpTicket.objects.get(pk=self.pk)
                old_status = old_instance.status
            except HelpTicket.DoesNotExist:
                pass

        # Update status based on prerequisite
        from core.services.HelpTicketPrerequisiteService import update_ticket_status_if_needed
        update_ticket_status_if_needed(self)

        super().save(*args, **kwargs)

        # If ticket was completed, update dependent tickets
        if old_status != "completed" and self.status == "completed":
            from core.services.HelpTicketPrerequisiteService import propagate_status_update
            propagate_status_update(self)

    @property
    def children_count(self) -> int:
        return self.children.count()
