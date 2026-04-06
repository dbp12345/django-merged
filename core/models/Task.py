# from django.conf import settings
from django.db import models
from treebeard.mp_tree import MP_Node

from core.utils import model_directory_path

STATUS_CHOICES = [
    ("new", "New"),
    ("processing", "Processing"),
    ("completed", "Completed"),
]


class Category(MP_Node):
    name = models.CharField(max_length=255)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    node_order_by = ["name"]

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    # def indented_name(self):
    #     pad = "&nbsp;&nbsp;" * max(self.get_depth() - 1, 0)
    #     return format_html(f"{pad}{self.name}")
    # indented_name.short_description = "Name"
    # indented_name.admin_order_field = "path"


class Task(models.Model):
    name = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    file = models.FileField("File", upload_to=model_directory_path, blank=True, null=True)
    notes = models.TextField(blank=True)
    # completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    completed_by = models.ForeignKey("company.Employees", on_delete=models.CASCADE, null=True, blank=True, related_name="task_as_employees", verbose_name="Completed by")
    status = models.CharField("Status", max_length=50, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["category"])
        ]

    def __str__(self):
        c = self.category.name if self.category else "-"
        return f"{self.name} — {c}"
