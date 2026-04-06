from django.views import View
from django.http import HttpRequest, HttpResponse
from pathlib import Path
from io import BytesIO
from django.conf import settings
from docxtpl import DocxTemplate
from company.models import Employees


class ExhibitDocsView(View):
    doc_path = (
        Path(settings.BASE_DIR)
        / "core"
        / "documents_templates"
        / "exhibit"
        / "1.1, Template, ODF summary Form 2025.docx"
    )

    def get(self, request: HttpRequest) -> HttpResponse:
        dispatch_id = request.GET.get("id")

        employee = (
            Employees.objects.get(id=dispatch_id)
        )

        dob_value = employee.get_param_value("DOB", property_type="SystemTime")
        dob_str = dob_value.strftime("%m/%d/%y") if dob_value else ""

        context = {
            "emp_file_as": employee.get_file_as,
            "emp_fn": employee.get_param_value("surname").upper(),
            "emp_ln": employee.get_param_value("given_name").upper(),
            "emp_mn": employee.get_param_value("middle_name").upper(),
            "emp_id": f"{employee.id:06d}",
            "emp_ica": employee.get_param_value("ICA Number").upper(),
            "emp_bd": dob_str,
        }

        students = []
        for student in employee.student_entries.all():
            name = student.training_class.course.training_type.name
            if "webinar" in name.lower():
                continue
            date_str = ""
            if student.training_class and student.training_class.date:
                date_str = student.training_class.date.strftime("%m/%y")
            students.append({
                "stu_name": name,
                "stu_date": date_str,
            })

        incidents = []
        for instance in employee.fire_run_entries.all().order_by('-start_date'):
            fire = instance.crew.fire if instance.crew and instance.crew.fire else None
            incident_name = ""
            incident_type = ""
            incident_agency = ""
            incident_state = ""
            if fire:
                incident_name = fire.incident_name
                incident_type = fire.incident_type
                incident_agency = fire.agency
                incident_state = fire.state

            date_str = ""
            if instance.start_date:
                date_str = instance.start_date.strftime("%m/%y")

            incidents.append({
                "inc_name": incident_name,
                "inc_type": incident_type,
                "inc_agency": incident_agency,
                "inc_state": incident_state,
                "inc_days": instance.operational_periods or "",
                "inc_date": date_str,
            })

        res = self.generate_docx_response(
            context,
            students,
            incidents,
            filename=f"Exhibit-N {employee.get_param_value('surname')}, {employee.get_param_value("given_name")}",
        )

        return res

    def generate_docx_response(self, context, students, incidents, filename="Exhibit-N") -> HttpResponse:
        doc = DocxTemplate(str(self.doc_path))
        context = {
            **context,
            "students": students,
            "incidents": incidents,
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
