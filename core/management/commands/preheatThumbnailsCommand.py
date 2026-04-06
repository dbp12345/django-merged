from django.core.management.base import BaseCommand
from sorl.thumbnail import get_thumbnail

from company.models import Employees_Pictures, Employees
from dispatch.models.VehicleCheckout import VehicleCheckout

class Command(BaseCommand):
    help = "preheatThumbnailsCommand"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(f"Run generated thumbnails."))

        count = 0
        for obj in VehicleCheckout.objects.iterator():
            for image_field in [
                obj.picture_front,
                obj.picture_rear,
                obj.picture_driver_side,
                obj.picture_passenger_side,
            ]:
                if image_field:
                    try:
                        obj.generate_thumbnail(image_field)
                        # self.stdout.write(image_field.url)
                        count += 1
                    except Exception as e:
                        self.stderr.write(self.style.WARNING(f"Thumbnail error for {image_field.name}: {e}"))

        for obj in Employees_Pictures.objects.iterator():
            for image_field in [
                obj.photo_exchange,
                obj.photo_privser_cropped_picture_for_red_card,
                # obj.photo_privser_passport_picture,
                obj.photo_privser_picture_at_field_training,
            ]:
                if image_field:
                    try:
                        obj.generate_thumbnail(image_field)
                        # self.stdout.write(image_field.url)
                        count += 1
                    except Exception as e:
                        self.stderr.write(self.style.WARNING(f"Thumbnail error for {image_field.name}: {e}"))

        for obj in Employees.objects.iterator():
            if obj.document:
                try:
                    get_thumbnail(obj.document, "200x200", crop=False, upscale=False, quality=60)
                    # self.stdout.write(obj.document.url)
                    count += 1
                    get_thumbnail(obj.document, "1540x1540", crop=False, upscale=False, quality=60)
                    # self.stdout.write(obj.document.url)
                    count += 1
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Thumbnail error for {obj.document.name}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Generated {count} thumbnails."))
