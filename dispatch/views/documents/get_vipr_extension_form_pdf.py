import json
from datetime import datetime

from django.shortcuts import render
from django.views import View
from django.http import HttpRequest, HttpResponse

from dispatch.models import Dispatch


class DispatchPdfExtensionFormView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        dispatch_id = request.GET.get("id")

        dispatch_instance = (
            Dispatch.objects
            .prefetch_related(
                "equipment_group",
                "equipment_group__truck_entries",
            )
            .select_related("fire", "crew")
            .get(id=dispatch_id)
        )

        incident_name = dispatch_instance.fire.incident_name if dispatch_instance.fire else ""
        incident_number = dispatch_instance.fire.fire_number if dispatch_instance.fire else ""
        company_name = dispatch_instance.company_rel.name if dispatch_instance.company_rel else ""

        crew = dispatch_instance.crew
        crew_name = crew.name if crew else ""

        context = {
            "Text1": incident_name,
            "Text2": "RESL",
            "Text3": "Operations",
            "Text4": "Contract Resource Extension / R&R / Crew Swap",
            "Text5": datetime.now().strftime("%m/%d/%Y"),
            "Text6": "",
            "Text7": company_name,
            "Text8": incident_number,
        }

        return render(request, "documents/vipr_extension_form_pdf.html", {
            "file_name": f"VIPR Extension Form {crew_name}.pdf",
            "pdf_context": json.dumps(context)
        })
