from django.db.models import Count, Q, OuterRef, Subquery, CharField
from django.urls import reverse
from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from urllib.parse import urlencode
import zipfile
from django.http import FileResponse
from io import BytesIO

from company.services.EmployeesService import get_employees_by_filter
from core.models import Saved_Filter
from core.services.StudentsDocsService import StudentsDocsService
from privser.models import Custom_Fields


@method_decorator(staff_member_required, name="dispatch")
class ExternalPdfView(View):
    template_name = "admin/external_pdf/external_pdf.html"
    required_courses = ["IS-100", "IS-700", "S-130", "S-190", "L-180", "Pack Test"]

    def get(self, request, *args, **kwargs):
        title = "External PDF"

        filters = list(Saved_Filter.objects.values("id", "name"))

        custom_fields_instance = Custom_Fields.objects.filter(
            privser_name__isnull=False,
            exchange_property__isnull=False,
            no_sync=False
        ).order_by("privser_name")

        employees_with_docs = get_employees_with_docs()

        employees = []
        for e in employees_with_docs:
            employees.append({
                "name": e.get_file_as,
                "admin_url": reverse("students_pdf_get") + "?" + urlencode({"id": str(e.id)})
            })

        context = {
            "title": title,
            "filters": filters,
            "required_courses": ExternalPdfView.required_courses,
            "custom_fields": custom_fields_instance,
            "employees": employees,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        employee_filter_id = request.POST.get("employee_filter")

        if employee_filter_id == "employees_with_docs":
            employees = get_employees_with_docs()
            print("get_employees_with_docs")
        else:
            employees = get_employees_by_filter(employee_filter_id)

        if action == "one_file":
            all_docs = []
            for emp in employees:
                all_docs.extend(StudentsDocsService.get_latest_docs_by_employee(emp.id))
            buffer = StudentsDocsService.build_combined_pdf(all_docs)
            return HttpResponse(
                buffer.getvalue(),
                content_type="application/pdf",
                headers={"Content-Disposition": 'attachment; filename="all.pdf"'}
            )
        elif action == "archive":
            zip_buffer = BytesIO()

            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for emp in employees:
                    pdf_buf = StudentsDocsService.generate_employee_pdf(emp.id)
                    file_name = StudentsDocsService.get_employee_file_name(emp.id) + ".pdf"
                    zf.writestr(file_name, pdf_buf.getvalue())

            zip_buffer.seek(0)
            return FileResponse(
                zip_buffer,
                content_type="application/zip",
                filename="external_pdf.zip"
            )


def get_employees_with_docs():
    from company.models import Employees, Employees_Parameters

    # employees_with_docs = (
    #     Employees.objects
    #     .annotate(
    #         matched_courses=Count(
    #             "student_entries",
    #             filter=Q(
    #                 student_entries__document__isnull=False,
    #                 student_entries__document__gt="",
    #                 student_entries__training_class__course__training_type__name__in=ExternalPdfView.required_courses,
    #             ),
    #             distinct=True,
    #         )
    #     )
    #     .filter(matched_courses=len(ExternalPdfView.required_courses))
    # )
    #
    # employees_with_docs = (
    #     Employees.objects.annotate(
    #         matched_courses=Count(
    #             "student_entries__training_class__course__training_type__name",
    #             filter=Q(
    #                 student_entries__document__isnull=False,
    #                 student_entries__document__gt="",
    #                 student_entries__training_class__course__training_type__name__in=ExternalPdfView.required_courses,
    #             ),
    #             distinct=True
    #         )
    #     ).filter(matched_courses=len(ExternalPdfView.required_courses))
    # )

    order_column_name = "surname"

    value_subquery = Employees_Parameters.objects.filter(
        employee=OuterRef("pk"),
        contacts_prop__property_name=order_column_name
    ).values("value")[:1]

    employees_with_docs = (
        Employees.objects
        .annotate(
            matched_course_count=Count(
                "student_entries__training_class__course__training_type__name",
                filter=Q(
                    student_entries__document__isnull=False,
                    student_entries__document__gt="",
                    student_entries__training_class__course__training_type__name__in=ExternalPdfView.required_courses
                ),
                distinct=True
            ),
            sorted_surname=Subquery(value_subquery, output_field=CharField())
        )
        .filter(matched_course_count=len(ExternalPdfView.required_courses))
        .order_by("sorted_surname")
    )

    return employees_with_docs
