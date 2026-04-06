from datetime import datetime

from django.views import View
from django.http import HttpRequest, HttpResponse

from pathlib import Path
from io import BytesIO
from django.conf import settings
from docxtpl import DocxTemplate

from dispatch.models import Dispatch


class DispatchDocsExtensionFormView(View):
    doc_path = Path(settings.BASE_DIR) / "core" / "documents_templates" / "manifests" / "Extension Request Form.docx"
    output_path = Path(settings.BASE_DIR) / "core" / "documents_templates" / "manifests" / "Extension Form.docx"

    def get(self, request: HttpRequest) -> HttpResponse:
        dispatch_id = request.GET.get("id")

        dispatch_instance = (
            Dispatch.objects
            .select_related("fire", "crew")
            .get(id=dispatch_id)
        )

        incident_name = dispatch_instance.fire.incident_name if dispatch_instance.fire else ""
        incident_number = dispatch_instance.fire.fire_number if dispatch_instance.fire else ""
        ec_number = dispatch_instance.ec_number or ""
        contractor = dispatch_instance.company_rel.name if dispatch_instance.company_rel else ""
        first_operational_period = dispatch_instance.first_operational_period.strftime("%m/%d/%Y") if dispatch_instance.first_operational_period else ""
        fourteenth_operational_period = dispatch_instance.fourteenth_operational_period.strftime("%m/%d/%Y") if dispatch_instance.fourteenth_operational_period else ""

        crew = dispatch_instance.crew
        if not crew:
            crew = dispatch_instance.crew_archived

        crew_name = crew.name if crew else ""
        crew_boss = crew.crew_boss if crew else ""

        context = {
            "contractor": contractor,
            "crew_boss": crew_boss.get_file_as if crew_boss else "",
            "ec_num": ec_number,
            "incident_name": incident_name,
            "incident_num": incident_number,
            "f_op_per": first_operational_period,
            "frth_op_per": fourteenth_operational_period,
            "date": datetime.now().strftime("%m/%d/%Y")
        }

        res = self.generate_docx_response(context, filename=f"Extension Form {crew_name}")

        return res

    def generate_docx_response(self, context, filename="Extension Form") -> HttpResponse:
        doc = DocxTemplate(str(self.doc_path))
        context = {
            **context,
        }
        doc.render(context)
        # doc.save(str(self.output_path)) # file save
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}.docx"'
        return response
