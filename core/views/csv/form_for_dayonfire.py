from django.conf import settings
from django.views import View
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from core.services.CsvForDayOnFireService import CsvForDayOnFireService
from core.tasks import import_handle_rows_dayonfire_task


class CsvDayonfireImportFormView(View):
    template_name = "csv/upload_dayonfire_form.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        title = "CSV DayOnFire Import"
        return render(request, self.template_name, {
            "title": title,
        })

    def post(self, request: HttpRequest) -> HttpResponse:
        title = "CSV DayOnFire Import"
        file = request.FILES.get("csv_file")
        if not file:
            return render(request, self.template_name, {"error": "File not uploaded"})

        importer = CsvForDayOnFireService()
        importer.set_file(file)
        importer.import_data()

        if settings.DEBUG:
            importer.handle_data()
        else:
            import_handle_rows_dayonfire_task.apply_async(
                kwargs={},
                queue="one_by_one"
            )

        return render(request, self.template_name, {
            "title": title,
        })
