import json

from django.shortcuts import render
from django.views import View
from django.http import HttpRequest, HttpResponse

from dispatch.models import Dispatch


class DispatchDocsPdfView(View):
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

        incident_name = dispatch_instance.fire.incident_name if dispatch_instance.fire else ""
        incident_number = dispatch_instance.fire.fire_number if dispatch_instance.fire else ""
        ec_number = dispatch_instance.ec_number
        ec_number = ec_number.replace("C-", "", 1) # если нужно убрать только первое вхождение "C-"
        resource_number = dispatch_instance.contract.resource_number if dispatch_instance.contract else ""

        context = {
            "Incident Name": incident_name,
            "Incident Number": incident_number,
            "Agreement Number": resource_number,
            "C": ec_number,
        }

        # crew
        crew = dispatch_instance.crew
        crew_name = crew.name if crew else ""

        context.update({
            "Crew Name": crew_name,
            "Hand Crew Manifest Y": True,
            "Hand Crew Manifest N": False,
            "Number of Employees": str(crew.employees.count() if crew else 0),
        })

        groups = list(dispatch_instance.equipment_group.all())
        saws_entries = [s for g in groups for s in g.saws_entries.all()]
        for i, saw in enumerate(saws_entries[:5], start=1):
            make = saw.make or ""
            model = saw.model or ""
            make_model = f"{make}/{model}" if make and model else make or model
            serial = saw.serial_number or ""

            context.update({
                f"A  MakeModel {i}": make_model, f"Serial {i}": serial,
            })

        radio_entries = [r for g in groups for r in g.radio_entries.all()]
        for i, radio in enumerate(radio_entries[:5], start=1):
            make = radio.make or ""
            model = radio.model or ""
            make_model = f"{make}/{model}" if make and model else make or model
            serial = radio.serial_number or ""

            if i == 1:
                context.update({
                    "Programmable Hand Held Radios F 43": make_model, "Serial 1_2": serial,
                })
            elif i == 2:
                context.update({
                    "1": make_model, "Serial 2_2": serial,
                })
            elif i == 3:
                context.update({
                    "2": make_model, "Serial 3_2": serial,
                })
            elif i == 4:
                context.update({
                    "3_3": make_model, "Serial 4_2": serial,
                })
            elif i == 5:
                context.update({
                    "4": make_model, "Serial 5_2": serial,
                })

        for key, value in context.items():
            if value is None:
                context[key] = ""

        # context.update({
        #     "Check Box6": True,
        #     "Check Box7": True,
        #     "Check Box8": False
        # })

        return render(request, "documents/pdf.html", {
            "file_name": f"ODF Eqp Manifest {crew_name}.pdf",
            "pdf_context": json.dumps(context)
        })
