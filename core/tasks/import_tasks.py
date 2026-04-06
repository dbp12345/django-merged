from celery import shared_task

from core.services.CsvForDayOnFireService import CsvForDayOnFireService
from core.services.CsvService import CsvService


@shared_task(
    name="import_handle_rows",
    queue="one_by_one"
)
def import_handle_rows_task(**kwargs):
    importer = CsvService()
    importer.handle_data()

@shared_task(
    name="import_handle_rows_dayonfire",
    queue="one_by_one"
)
def import_handle_rows_dayonfire_task(**kwargs):
    importer = CsvForDayOnFireService()
    importer.handle_data()
