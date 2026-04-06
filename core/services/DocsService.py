from pathlib import Path
from io import BytesIO
from django.conf import settings
from django.http import HttpResponse
from docxtpl import DocxTemplate


class DocxService: # ПРОСТО ДЛЯ ПРИМЕРА ВИСИТ, ВООБЩЕ УДАЛИТЬ ЕГО МОЖНО И НУЖНО
    doc_path = Path(settings.BASE_DIR) / "core" / "documents_templates" / "manifests" / "Hand Crew Manifest 2.0.docx"
    output_path = Path(settings.BASE_DIR) / "core" / "documents_templates" / "manifests" / "filled_manifest.docx"

    def __init__(self):
        self.context = {}
        self.employees = []
        self.vehicles = []

    def setContext(self, context: dict):
        self.context = context

    def setEmployeesList(self, employees: list[dict]):
        self.employees = employees

    def setVehiclesList(self, vehicles: list[dict]):
        self.vehicles = vehicles

    def _render_doc(self):
        doc = DocxTemplate(str(self.doc_path))
        context = {
            **self.context,
            "employees": self.employees,
            "vehicles": self.vehicles,
        }
        doc.render(context)
        return doc

    def render_docx_to_file(self, output_path: str | Path = None):
        output_path = output_path or self.output_path
        doc = self._render_doc()
        doc.save(str(output_path))

    def generate_docx_response(self, filename="filled_manifest") -> HttpResponse:
        doc = self._render_doc()
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}.docx"'
        return response
