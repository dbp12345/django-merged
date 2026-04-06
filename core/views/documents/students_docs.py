from django.views import View
from django.http import HttpRequest, HttpResponse

from core.services.StudentsDocsService import StudentsDocsService


class StudentsDocsView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        employee_id = request.GET.get("id")
        docs = StudentsDocsService.get_latest_docs_by_employee(employee_id)
        buffer = StudentsDocsService.build_combined_pdf(docs)
        file_name = StudentsDocsService.get_employee_file_name(employee_id)

        return HttpResponse(
            buffer.getvalue(),
            content_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{file_name}.pdf"'}
        )
