from io import BytesIO
from pathlib import Path
from PIL import Image
from typing import List

from pypdf import PdfWriter, PdfReader
from company.models import Student, Employees


class StudentsDocsService:
    @staticmethod
    def get_latest_docs_by_employee(employee_id) -> List[Student]:
        docs = (
            Student.objects
            .filter(employee_id=employee_id)
            .exclude(document="")
            .exclude(training_class__course__training_type__name__in=["S-190", "L-180"])
            .select_related("training_class__course")
        )

        latest_by_course = {}
        for s in docs:
            course_id = s.training_class.course_id
            current = latest_by_course.get(course_id)
            if not current or (s.training_class.date or "") > (current.training_class.date or ""):
                latest_by_course[course_id] = s

        return list(latest_by_course.values())

    @staticmethod
    def build_combined_pdf(docs: List[Student]) -> BytesIO:
        writer = PdfWriter()

        for s in docs:
            try:
                path = Path(s.document.path)
                if not path.exists():
                    continue

                ext = path.suffix.lower()

                if ext == ".pdf":
                    reader = PdfReader(str(path))
                    for page in reader.pages:
                        writer.add_page(page)

                elif ext in [".png", ".jpg", ".jpeg"]:
                    image = Image.open(path).convert("RGB")
                    image_pdf = BytesIO()
                    image.save(image_pdf, format="PDF")
                    image_pdf.seek(0)

                    img_reader = PdfReader(image_pdf)
                    for page in img_reader.pages:
                        writer.add_page(page)

            except Exception:
                continue

        buffer = BytesIO()
        writer.write(buffer)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_employee_pdf(employee_id: int) -> BytesIO:
        docs = StudentsDocsService.get_latest_docs_by_employee(employee_id)
        return StudentsDocsService.build_combined_pdf(docs)

    @staticmethod
    def get_employee_file_name(employee_id):
        e = Employees.objects.get(id=employee_id)
        return f"{e.get_param_value("surname")}, {e.get_param_value("given_name")}_{e.get_param_value("job_title")}"
