from django.utils import timezone
from django.views import View
from django.http import HttpRequest, HttpResponse

from pathlib import Path
from io import BytesIO
from django.conf import settings
from docxtpl import DocxTemplate

from company.models import JobTitle
from core.services.DotDeterminantService import DotDeterminantService
from dispatch.models import Dispatch
from exchange.models import Contacts_Prop


class DispatchDocsView(View):
    doc_path = Path(settings.BASE_DIR) / "core" / "documents_templates" / "manifests" / "Hand Crew Manifest 2.0.docx"
    output_path = Path(settings.BASE_DIR) / "core" / "documents_templates" / "manifests" / "Hand Crew Manifest.docx"

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

        incident_ordering = ""
        incident_name = dispatch_instance.fire.incident_name if dispatch_instance.fire else ""
        incident_number = dispatch_instance.fire.fire_number if dispatch_instance.fire else ""
        resource_number = dispatch_instance.ec_number or ""
        contractor = dispatch_instance.company_rel.name if dispatch_instance.company_rel else ""
        dispatch_address = dispatch_instance.contract.dispatch_address if dispatch_instance.contract else ""
        contract_number = dispatch_instance.contract.number if dispatch_instance.contract else ""

        crew = dispatch_instance.crew
        crew_name = crew.name if crew else ""

        context = {
            "incident_ordering": incident_ordering,
            "incident_name": incident_name,
            "incident_number": incident_number,
            "resource_number": resource_number,
            "contractor": contractor,
            "dispatch_address": dispatch_address,
            "contract_number": contract_number,
        }

        groups = list(dispatch_instance.equipment_group.all())
        truck_entries = [t for g in groups for t in g.truck_entries.all()]

        employees_entries = crew.employees.all() if crew else []

        vehicles = []
        for truck_entry in truck_entries:
            make = truck_entry.make or ""
            model = truck_entry.model or ""
            # truck_emp_license_state_number = truck_entry.empl or "" #employee.get_param_value("Driver's License State, Number")
            if make and model:
                make_model = f"{make}/{model}"
            else:
                make_model = make or model

            for employee_drv in employees_entries:
                veh_drv_2 = employee_drv.get_param_value(property_name="MSPA Expiration Date", property_type=Contacts_Prop.TypeChoices.SYSTEM_TIME)
                if veh_drv_2 and veh_drv_2.date() > timezone.localdate():
                    print("veh_drv_2: ", veh_drv_2.strftime("%m/%d/%Y"))

                    vehicles.append({
                        "veh_drv_1": employee_drv.get_file_as or "",
                        "veh_drv_2": veh_drv_2.strftime("%m/%d/%Y") if veh_drv_2 else "",
                        "veh_drv_3": employee_drv.get_param_value(property_name="Driver's License State, Number") or "",
                        "veh_m": make_model or "",
                        "veh_year": truck_entry.year or "",
                        "veh_lic": truck_entry.license_plate or ""
                    })

        if not vehicles:
            for truck_entry in truck_entries:
                make = truck_entry.make or ""
                model = truck_entry.model or ""
                if make and model:
                    make_model = f"{make}/{model}"
                else:
                    make_model = make or model
                vehicles.append({
                    "veh_drv_1": "",
                    "veh_drv_2": "",
                    "veh_drv_3": "",
                    "veh_m": make_model or "",
                    "veh_year": truck_entry.year or "",
                    "veh_lic": truck_entry.license_plate or ""
                })

        employees = []
        i = 0
        for employee in employees_entries:
            female = employee.get_param_value("Female (Company Manifest)")
            dot_season = DotDeterminantService.get_dot_season(employee=employee)
            i = i + 1
            color_str = dot_season.color
            employees.append({
                "emp_nun": str(i),
                # CHANGED: fix quote nesting in f-string
                "emp_name": employee.get_file_as,
                # "emp_name": f"{employee.get_param_value('surname')}, {employee.get_param_value('given_name')}",
                "emp_m": "" if female else "X",
                "emp_f": female if female else "",
                "emp_ica": employee.get_param_value("ICA Number") or "",
                "emp_ipos": normalize_job_title(employee.get_param_value("job_title")),
                "emp_sc": employee.get_param_value("Sawyer") or "",
                "emp_emt": "",
                "emp_exp": color_str[0].upper() if color_str else ""
            })

        employees = _order_employees(employees)

        res = self.generate_docx_response(context, employees, vehicles, filename=f"Hand Crew Manifest {crew_name}")

        return res

    def generate_docx_response(self, context, employees, vehicles, filename="Hand Crew Manifest") -> HttpResponse:
        doc = DocxTemplate(str(self.doc_path))
        context = {
            **context,
            "employees": employees,
            "vehicles": vehicles,
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


def normalize_job_title(raw_title: str) -> str:
    if not raw_title:
        return ""

    t = raw_title.upper()

    if "FFT1T" in t or "(F1T" in t:
        return JobTitle.FFT1T.value
    if "FFT1" in t:
        return JobTitle.FFT1.value
    if "FFT2" in t:
        return JobTitle.FFT2.value
    if "CRWBT" in t:
        return JobTitle.CRWBT.value
    if "CRWB" in t:
        return JobTitle.CRWB.value
    if "ENGBT" in t:
        return JobTitle.ENGBT.value
    if "ENGB" in t:
        return JobTitle.ENGB.value
    if "REP" in t:
        return JobTitle.REP.value

    return ""


def _order_employees(employees: list[dict]) -> list[dict]:
    # group by position code
    crwb = [e for e in employees if (e.get("emp_ipos") == "CRWB")]
    crwbt = [e for e in employees if (e.get("emp_ipos") == "CRWBT")]
    engb = [e for e in employees if (e.get("emp_ipos") == "ENGB")]
    engbt = [e for e in employees if (e.get("emp_ipos") == "ENGBT")]
    fft1 = [e for e in employees if (e.get("emp_ipos") == "FFT1")]
    others = [e for e in employees if e not in crwb + crwbt + engb + engbt + fft1]

    # base order without FFT1 (they go by fixed slots later)
    base = crwb + crwbt + engb + engbt + others

    # place FFT1 at exact 1-based positions [2, 11, 20]
    target_positions = [2, 11, 20]
    res = list(base)
    i_fft = 0
    for pos in target_positions:
        if i_fft >= len(fft1):
            break
        idx = max(0, pos - 1)
        if idx >= len(res):
            res.extend([] for _ in range(idx - len(res)))  # no-op, keeps logic explicit
            res.append(fft1[i_fft])
        else:
            res.insert(idx, fft1[i_fft])
        i_fft += 1

    # append any remaining FFT1 after all forced positions (keep relative order)
    if i_fft < len(fft1):
        res.extend(fft1[i_fft:])

    # strip accidental Nones (not expected, but safe)
    res = [e for e in res if isinstance(e, dict)]

    # renumber sequentially
    for i, e in enumerate(res, start=1):
        e["emp_nun"] = str(i)

    return res
