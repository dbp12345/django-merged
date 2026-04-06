from django.views import View
from django.http import JsonResponse, HttpRequest, HttpResponse

from core.services.CsvForDayOnFireService import CsvForDayOnFireService


class CsvForDayOnFireImportStatusView(View):
    template_name = "csv/upload_dayonfire_form.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        errors = "errors" in request.GET
        importer = CsvForDayOnFireService()
        if errors:
            print("importer.errors()", importer.get_errors())
            return JsonResponse(importer.get_errors(), safe=False)

        return JsonResponse(importer.get_status())
