from collections import defaultdict

from pwa_crwb.decorators import employee_required

from django.db.models import Subquery, OuterRef, CharField, DateField, F
from django.shortcuts import render
from company.models import (
    Employees,
    DispatchStatus,
    Student,
    Employees_Parameters, TrainingClass,
)


@employee_required
def crew_view(request):
    employee = Employees.objects.get(id=request.session["employee_id"])

    job_title = employee.get_job_title or ""
    if "crwb" not in job_title.lower() and "engb" not in job_title.lower():
        context = {
            "employee": employee,
            "crews_list": [],
        }
        return render(request, "pwa_crwb/crwb_front/crew.html", context)

    crew = employee.fire_crew

    def annotated_employees_qs(base_qs):
        return base_qs.annotate(
            # student_class_date=Subquery(
            #     Student.objects.filter(employee=OuterRef("pk"))
            #     .order_by("-updated_at")
            #     .values("training_class__date")[:1],
            #     output_field=DateField()
            # ),
            s212_class_date=Subquery(
                TrainingClass.objects
                .filter(
                    student_entries__employee=OuterRef("pk"),
                    course__training_type__name="S-212",
                )
                .order_by(F("date").desc(nulls_last=True), "-updated_at")  # tie-breaker
                .values("date")[:1],
                output_field=DateField()
            ),
            dispatch_status=Subquery(
                Employees_Parameters.objects.filter(
                    employee=OuterRef("pk"),
                    contacts_prop__property_name="Dispatch Call Status"
                ).values("value"),
                output_field=CharField()
            ),
            mspa_expiration_date=Subquery(
                Employees_Parameters.objects.filter(
                    employee=OuterRef("pk"),
                    contacts_prop__property_name="MSPA Expiration Date"
                ).values("value_date"),
                output_field=DateField()
            ),
            emt_value=Subquery(
                Employees_Parameters.objects.filter(
                    employee=OuterRef("pk"),
                    contacts_prop__property_name="EMT"
                ).values("value"),
                output_field=CharField()
            ),
            job_title_annotate=Subquery(
                Employees_Parameters.objects.filter(
                    employee=OuterRef("pk"),
                    contacts_prop__property_name="job_title"
                ).values("value"),
                output_field=CharField()
            ),
            surname_annotate=Subquery(
                Employees_Parameters.objects.filter(
                    employee=OuterRef("pk"),
                    contacts_prop__property_name="surname"
                ).values("value"),
                output_field=CharField()
            ),
            given_name_annotate=Subquery(
                Employees_Parameters.objects.filter(
                    employee=OuterRef("pk"),
                    contacts_prop__property_name="given_name"
                ).values("value"),
                output_field=CharField()
            ),
            middle_name_annotate=Subquery(
                Employees_Parameters.objects.filter(
                    employee=OuterRef("pk"),
                    contacts_prop__property_name="middle_name"
                ).values("value"),
                output_field=CharField()
            ),
            email_annotate=Subquery(
                Employees_Parameters.objects.filter(
                    employee=OuterRef("pk"),
                    contacts_prop__property_name="email"
                ).values("value"),
                output_field=CharField()
            ),
        ).select_related("fire_crew").order_by("surname_annotate", "given_name_annotate", "middle_name_annotate", "email_annotate")

    # Всегда включаем свою crew, если есть
    base_qs = Employees.objects.filter(fire_crew=crew) if crew else Employees.objects.none()
    employees_main_qs = annotated_employees_qs(base_qs)

    # Добавляем "On Fire", если это админ
    if employee.id == 49622:
        on_fire_ids = (
            Employees.objects
            .filter(
                fire_crew__visible=True,
                fire_crew__isnull=False,
                employees_parameters_entries__contacts_prop__property_name="Dispatch Call Status",
                employees_parameters_entries__value="On Fire",
            )
            .exclude(fire_crew=crew)
            .values_list("id", flat=True)
        )

        employees_on_fire_qs = annotated_employees_qs(
            Employees.objects.filter(id__in=on_fire_ids)
        )

        combined_qs = list(employees_main_qs) + list(employees_on_fire_qs)
    else:
        combined_qs = list(employees_main_qs)

    crew_dict = defaultdict(list)
    for emp in combined_qs:
        crew_name = emp.fire_crew.name if emp.fire_crew else "No Crew"

        surname = emp.surname_annotate
        given_name = emp.given_name_annotate
        middle_name = emp.middle_name_annotate
        if surname:
            rest = " ".join(part for part in [given_name, middle_name] if part)
            file_as = f"{surname}, {rest}" if rest else surname
        else:
            file_as = " ".join(part for part in [given_name, middle_name] if part)

        crew_dict[crew_name].append({
            "id": emp.id,
            "one": file_as or emp.email_annotate,
            "two": emp.job_title_annotate,
            "three": emp.s212_class_date.strftime("%m/%d/%Y") if emp.s212_class_date else None,
            "four": emp.mspa_expiration_date.strftime("%m/%d/%Y") if emp.mspa_expiration_date else None,
            "five": emp.emt_value,
            "status_color": DispatchStatus.get_color_by_label(emp.dispatch_status) or "white",
        })

    main_crew_name = getattr(crew, "name", None)

    crews_list = []

    if main_crew_name and main_crew_name in crew_dict:
        crews_list.append({
            "crew_name": main_crew_name,
            "employees": crew_dict.pop(main_crew_name),
        })

    # Остальные команды в алфавитном порядке
    for name, crew_emps in sorted(crew_dict.items(), key=lambda x: x[0]):
        crews_list.append({
            "crew_name": name,
            "employees": crew_emps,
        })

    context = {
        "employee": employee,
        "crews_list": crews_list,
    }

    return render(request, "pwa_crwb/crwb_front/crew.html", context)
