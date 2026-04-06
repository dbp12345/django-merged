import json

from django.shortcuts import render
from django.views import View
from django.http import HttpRequest, HttpResponse

from dispatch.models import Dispatch


class DispatchPdfViprEqpView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        dispatch_id = request.GET.get("id")

        dispatch_instance = (
            Dispatch.objects
            .prefetch_related(
                "equipment_group",
                "equipment_group__saws_entries",
                "equipment_group__radio_entries",
            )
            .select_related("fire", "crew")
            .get(id=dispatch_id)
        )

        crew = dispatch_instance.crew
        company_name = dispatch_instance.company_rel.name if dispatch_instance.company_rel else ""
        crew_name = crew.name if crew else ""
        context = {
            "Company Name": company_name,
            "Vehicle sn or Unique ID": crew_name,
        }

        groups = list(dispatch_instance.equipment_group.all())
        saws_entries = [s for g in groups for s in g.saws_entries.all()]
        for i, saw in enumerate(saws_entries[:6], start=1):
            make = saw.make or ""
            model = saw.model or ""
            make_model = f"{make}/{model}" if make and model else make or model
            serial = saw.serial_number or ""

            context.update({
                f"Extra items vendor s may carry {i}": f"Saw {make_model}, {serial}"
            })

        radio_entries = [r for g in groups for r in g.radio_entries.all()]
        for i, radio in enumerate(radio_entries[:6], start=1):
            make = radio.make or ""
            model = radio.model or ""
            make_model = f"{make}/{model}" if make and model else make or model
            serial = radio.serial_number or ""

            context.update({
                f"Extra items vendor r may carry {i}": f"Radio {make_model}, {serial}"
            })

        for key, value in context.items():
            if value is None:
                context[key] = ""

        return render(request, "documents/vipr_eqp_pdf.html", {
            "file_name": f"VIPR Eqp Manifest {crew_name}.pdf",
            "pdf_context": json.dumps(context)
        })
