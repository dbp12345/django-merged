import os

from django.db import models
from django.utils.html import format_html
from sorl.thumbnail import get_thumbnail

from core import settings
from core.utils import model_directory_path_photo
from company.models import Employees


class Employees_Pictures(models.Model):
    THUMBNAIL_OPTIONS = {
        "geometry": "200x200",
        "crop": False,
        "upscale": False,
        "quality": 60,
    }

    employee = models.ForeignKey(
        Employees,
        on_delete=models.CASCADE,
        related_name="employees_pictures_entries",
        db_index=True,
        db_constraint=False,
        db_column="employees_id"
    )
    photo_exchange = models.ImageField(upload_to=model_directory_path_photo, blank=True, null=True, verbose_name="Photo exc")
    photo_privser_cropped_picture_for_red_card = models.ImageField(upload_to=model_directory_path_photo, blank=True, null=True, verbose_name="Photo priv cropped picture for red card")
    photo_privser_passport_picture = models.ImageField(upload_to=model_directory_path_photo, blank=True, null=True, verbose_name="Photo priv passport")
    photo_privser_picture_at_field_training = models.ImageField(upload_to=model_directory_path_photo, blank=True, null=True, verbose_name="Photo priv picture at field training")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return ""

    class Meta:
        verbose_name = "Photo"
        verbose_name_plural = "Photos"

    def photo_exchange_preview(self):
        if self.photo_exchange:
            thumb = self.generate_thumbnail(self.photo_exchange)
            return format_html(
                '<a href="{}" target="_blank"><img loading="lazy" src="{}" /></a>',
                self.photo_exchange.url,
                thumb.url,
            )
        return format_html('<div class="img-click">No Image</div>')

    def photo_privser_cropped_picture_for_red_card_preview(self):
        if self.photo_privser_cropped_picture_for_red_card:
            thumb = self.generate_thumbnail(self.photo_privser_cropped_picture_for_red_card)
            return format_html(
                '<a href="{}" target="_blank"><img loading="lazy" src="{}" /></a>',
                self.photo_privser_cropped_picture_for_red_card.url,
                thumb.url,
            )
        from django.urls import reverse
        from urllib.parse import urlencode
        url_edit = reverse("pictures_cropped_edit") + "?" + urlencode({"id": str(self.id)})
        return format_html("<a href='{}' target='_blank' rel='noreferrer noopener'>{}</a>", url_edit, "Create Photo")

    def photo_privser_passport_picture_preview(self):
        if self.photo_privser_passport_picture:
            thumb = self.generate_thumbnail(self.photo_privser_passport_picture)
            return format_html(
                '<a href="{}" target="_blank"><img loading="lazy" src="{}" /></a>',
                self.photo_privser_passport_picture.url,
                thumb.url,
            )
        return format_html('<div class="img-click">No Image</div>')

    def photo_privser_picture_at_field_training_preview(self):
        if self.photo_privser_picture_at_field_training:
            thumb = self.generate_thumbnail(self.photo_privser_picture_at_field_training)
            return format_html(
                '<a href="{}" target="_blank"><img loading="lazy" src="{}" /></a>',
                self.photo_privser_picture_at_field_training.url,
                thumb.url,
            )
        return format_html('<div class="img-click">No Image</div>')

    def generate_thumbnail(self, image_field):
        if not image_field:
            return None
        options = self.THUMBNAIL_OPTIONS.copy()
        geometry = options.pop("geometry")
        return get_thumbnail(image_field, geometry, **options)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.clean_old_versions()

    def clean_old_versions(self):
        folder_path = os.path.join(
            self._meta.model_name,
            str(self.employee.id)
        )
        abs_folder_path = os.path.join(settings.MEDIA_ROOT, folder_path)

        if not os.path.isdir(abs_folder_path):
            return

        current_files = {
            os.path.basename(getattr(f, "name", ""))
            for f in [
                self.photo_exchange,
                self.photo_privser_cropped_picture_for_red_card,
                self.photo_privser_passport_picture,
                self.photo_privser_picture_at_field_training
            ]
            if f and getattr(f, "name", None)
        }

        for fname in os.listdir(abs_folder_path):
            fpath = os.path.join(abs_folder_path, fname)
            if fname not in current_files and os.path.isfile(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass
