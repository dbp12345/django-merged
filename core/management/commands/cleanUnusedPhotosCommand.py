from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "cleanUnusedPhotosCommand"

    # "Удаляет неиспользуемые картинки из employees_pictures"
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(f"Run cleanUnusedPhotosCommand."))

        # Чат gpt предложил вариант как чистить ненужные картинки, которых нету в бд.
        # Совсем не тестировал и не настраивал. Это просто копия из чата для памяти.

        # Тогда вот готовая Django management-команда,
        # которая чистит неиспользуемые картинки из папки uploaded_documents/employees_pictures/, сверяясь с полями модели Employees_Pictures.

        # media_root = Path(settings.MEDIA_ROOT)
        # pictures_dir = media_root / "uploaded_documents" / "employees_pictures"
        #
        # if not pictures_dir.exists():
        #     self.stdout.write(self.style.WARNING("Папка с фото не найдена."))
        #     return
        #
        # # Собираем все пути из БД
        # used_files = set()
        # for obj in Employees_Pictures.objects.all():
        #     for field in [
        #         "photo_exchange",
        #         "photo_privser_cropped_picture_for_red_card",
        #         "photo_privser_passport_picture",
        #         "photo_privser_picture_at_field_training",
        #     ]:
        #         f = getattr(obj, field)
        #         if f and f.name:
        #             used_files.add(media_root / f.name)
        #
        # # Удаляем неиспользуемые файлы
        # removed_count = 0
        # for file_path in pictures_dir.glob("*"):
        #     if file_path not in used_files:
        #         try:
        #             file_path.unlink()
        #             removed_count += 1
        #             self.stdout.write(f"Удалён: {file_path}")
        #         except Exception as e:
        #             self.stderr.write(f"Ошибка при удалении {file_path}: {e}")
        #
        # self.stdout.write(self.style.SUCCESS(f"Удалено файлов: {removed_count}"))

        self.stdout.write(self.style.SUCCESS(f"End cleanUnusedPhotosCommand."))
