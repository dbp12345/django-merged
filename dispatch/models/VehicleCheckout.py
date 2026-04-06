from django.db import models
from django.utils.html import format_html
from sorl.thumbnail import get_thumbnail
from company.models import Employees
from core.utils import model_directory_path
from dispatch.models.Dispatch import Truck

CHK_STATUS = [
    ("Checkout", "Checkout"),
    ("Returning", "Returning"),
]


class VehicleCheckout(models.Model):
    THUMBNAIL_OPTIONS = {
        "geometry": "80x80",
        "crop": False,
        "upscale": False,
        "quality": 60,
    }

    truck = models.ForeignKey(Truck, on_delete=models.SET_NULL, related_name="vehicle_checkout_entries", null=True, blank=True)
    employee = models.ForeignKey(Employees, on_delete=models.SET_NULL, related_name="vehicle_checkout_entries", null=True, blank=True)

    milage = models.IntegerField(blank=True, null=True)
    license_plate = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(
        max_length=25,
        choices=CHK_STATUS,
        blank=False,
        null=False,
        default="Checkout",
    )

    picture_front = models.ImageField(upload_to=model_directory_path, blank=True, null=True)
    picture_rear = models.ImageField(upload_to=model_directory_path, blank=True, null=True)
    picture_driver_side = models.ImageField(upload_to=model_directory_path, blank=True, null=True)
    picture_passenger_side = models.ImageField(upload_to=model_directory_path, blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def picture_front_preview(self):
        if self.picture_front:
            thumb = self.generate_thumbnail(self.picture_front)
            return format_html(
                '<a href="{}" target="_blank" style="cursor: zoom-in;" onclick="event.preventDefault(); showModal(this.getAttribute(\'href\'))"><img loading="lazy" src="{}" /></a>',
                self.picture_front.url,
                thumb.url
            )
        return ""

    def picture_rear_preview(self):
        if self.picture_rear:
            thumb = self.generate_thumbnail(self.picture_rear)
            return format_html(
                '<a href="{}" target="_blank" style="cursor: zoom-in;" onclick="event.preventDefault(); showModal(this.getAttribute(\'href\'))"><img loading="lazy" src="{}" /></a>',
                self.picture_rear.url,
                thumb.url,
            )
        return ""

    def picture_driver_side_preview(self):
        if self.picture_driver_side:
            thumb = self.generate_thumbnail(self.picture_driver_side)
            return format_html(
                '<a href="{}" target="_blank" style="cursor: zoom-in;" onclick="event.preventDefault(); showModal(this.getAttribute(\'href\'))"><img loading="lazy" src="{}" /></a>',
                self.picture_driver_side.url,
                thumb.url,
            )
        return ""

    def picture_passenger_side_preview(self):
        if self.picture_passenger_side:
            thumb = self.generate_thumbnail(self.picture_passenger_side)
            return format_html(
                '<a href="{}" target="_blank" style="cursor: zoom-in;" onclick="event.preventDefault(); showModal(this.getAttribute(\'href\'))"><img loading="lazy" src="{}" /></a>',
                self.picture_passenger_side.url,
                thumb.url,
            )
        return ""

    class Meta:
        verbose_name = "Vehicle Checkout"
        verbose_name_plural = "Vehicle Checkouts"

    def __str__(self):
        truck_str = str(self.truck) if self.truck else "Unknown Truck"
        employee_str = str(self.employee) if self.employee else "Unknown Employee"
        return f"{employee_str} — {truck_str} — {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def generate_thumbnail(self, image_field):
        if not image_field:
            return None
        options = self.THUMBNAIL_OPTIONS.copy()
        geometry = options.pop("geometry")
        return get_thumbnail(image_field, geometry, **options)
