from django.views import View
from django.http import JsonResponse, HttpRequest, HttpResponse

from core.services.CsvService import CsvService


class CsvImportStatusView(View):
    template_name = "csv/upload_form.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        errors = "errors" in request.GET
        importer = CsvService()
        if errors:
            print("importer.errors()", importer.get_errors())
            return JsonResponse(importer.get_errors(), safe=False)

        return JsonResponse(importer.get_status())
