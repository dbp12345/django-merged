from django.db.models import Subquery, OuterRef
from django.urls import reverse
from django.views import View
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from company.models import (
    Employees,
    Employees_Pictures,
    Student,
    Employees_Parameters,
    FireCrew,
    Company,
)
from core.services.DotDeterminantService import DotDeterminantService
from dispatch.models import Dispatch


class CrewCardsView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        crew_id = request.GET.get("crew")

        if not crew_id:
            return HttpResponse("Missing crew_id", status=400)

        crew = FireCrew.objects.only("id", "name").filter(id=crew_id).first()

        if not crew:
            return HttpResponse("Crew not found", status=404)

        employees_ids = list(
            Employees.objects.filter(fire_crew_id=crew.id).values_list("id", flat=True)
        )
        title = crew.name

        return render(
            request,
            "cards/crew_cards.html",
            context={
                "title": title,
                "ids": employees_ids,
            },
        )


class CardsView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        employee_instance = None
        # crew_list = None
        user_id = request.GET.get("id")
        email = request.GET.get("email")
        # crew_id = request.GET.get("crew")

        # if crew_id:
        #     crew_employee = Employees.objects.filter(fire_crew=crew_id)
        #     crew_list = [{
        #         "id": e.id,
        #         "email": e.email,
        #         "name": e.name,
        #         "active": False,
        #         "url": reverse("cards_create") + "?" + urlencode({"crew": crew_id, "id": e.id}),
        #     } for e in crew_employee]
        #
        #     email = None
        #     if not user_id and crew_list:
        #         user_id = str(crew_list[0]["id"])
        #
        #     for item in crew_list:
        #         item["active"] = str(item["id"]) == str(user_id)

        if email:
            employee_instance = Employees.objects.filter(email=email).first()

        if user_id:
            employee_instance = Employees.objects.filter(id=user_id).first()

        if not employee_instance:
            return HttpResponse("Employee not found", status=403)

        employee_url = reverse(
            "admin:%s_%s_change"
            % (employee_instance._meta.app_label, employee_instance._meta.model_name),
            args=[employee_instance.pk],
        )

        rows = []
        q_rows = []
        photo = None
        employees_pictures = Employees_Pictures.objects.filter(
            employee=employee_instance
        ).first()
        if (
            employees_pictures
            and employees_pictures.photo_privser_cropped_picture_for_red_card
        ):
            photo = employees_pictures.photo_privser_cropped_picture_for_red_card
        elif (
            employees_pictures
            and employees_pictures.photo_privser_picture_at_field_training
        ):
            photo = employees_pictures.photo_privser_picture_at_field_training
        elif employee_instance.document:
            photo = employee_instance.document
        # title = f"{employee_instance.name} [{employee_instance.email}]"
        title = employee_instance.get_file_as

        ica_number = Employees_Parameters.objects.filter(
            employee=employee_instance, contacts_prop__property_name="ICA Number"
        ).first()
        ica_number_value = "-"
        if ica_number:
            ica_number_value = ica_number.value
        rows.append(["ID#:", ica_number_value])

        employees_qs = Employees.objects.annotate(
            pack_test_date=Subquery(
                Student.objects.filter(
                    employee=OuterRef("pk"),
                    training_class__course__training_type__name="Pack Test",
                )
                .order_by("-training_class__date")
                .values("training_class__date")[:1]
            )
        ).get(pk=employee_instance.pk)
        if employees_qs.pack_test_date:
            rows.append(["WCFT:", employees_qs.pack_test_date.strftime("%m/%d/%Y")])

        iqs = Employees_Parameters.objects.filter(
            employee=employee_instance,
            contacts_prop__property_name="ICS Certification Date",
        ).first()
        iqs_value = "-"
        if iqs and iqs.value_date:
            iqs_value = iqs.value_date.strftime("%m/%d/%Y")

        employees_qs = Employees.objects.annotate(
            last_rt130_date=Subquery(
                Student.objects.filter(
                    employee=OuterRef("pk"),
                    training_class__course__training_type__name="RT-130",
                )
                .order_by("-training_class__date")
                .values("training_class__date")[:1]
            )
        ).get(pk=employee_instance.pk)
        if employees_qs.last_rt130_date:
            rows.append(["RT-130:", employees_qs.last_rt130_date.strftime("%m/%d/%Y")])
        else:
            rows.append(["ICS:", iqs_value])

        dot_season = DotDeterminantService.get_dot_season(employee=employees_qs)

        rows.append(["English:", "Yes"])
        rows.append(["Seasons:", dot_season.periods_count])
        # rows.append(["Exp. code", ""])

        job_title = dot_season.job_title
        job_title = job_title.split()[0] if job_title and job_title.strip() else ""

        q_rows.append([job_title, iqs_value])

        employees_qs = Employees.objects.annotate(
            sawyer_date=Subquery(
                Student.objects.filter(
                    employee=OuterRef("pk"),
                    training_class__course__training_type__name="S-212",
                )
                .order_by("-training_class__date")
                .values("training_class__date")[:1]
            )
        ).get(pk=employee_instance.pk)
        if employees_qs.sawyer_date:
            q_rows.append(["Sawyer", employees_qs.sawyer_date.strftime("%m/%d/%Y")])

        first_aid_cpr = Employees_Parameters.objects.filter(
            employee=employee_instance, contacts_prop__property_name="First Aid/CPR"
        ).first()
        if first_aid_cpr and first_aid_cpr.value_date:
            q_rows.append(
                [
                    "First Aid/CPR",
                    f"Exp.{first_aid_cpr.value_date.strftime('%m/%d/%Y')}",
                ]
            )

        selected_company = None
        dispatch = (
            Dispatch.objects.filter(crew=employee_instance.fire_crew)
            .order_by("-updated_at")
            .first()
        )
        if dispatch and dispatch.company_rel:
            selected_company = dispatch.company_rel

        return render(
            request,
            "cards/fragment.html",
            context={
                "title": title,
                # "crew_list": crew_list,
                "employee_url": employee_url,
                "employee_name": employee_instance.get_file_as,
                "employee_email": employee_instance.get_email,
                "employee_phone": employee_instance.get_phone,
                "employee_status": employee_instance.get_param_value(
                    "Availability status"
                ),
                "rows": rows,
                "q_rows": q_rows,
                "color": dot_season.color,
                "company_names": list(Company.objects.values_list("name", flat=True)),
                "selected_company": selected_company,
                "pictures": photo,
            },
        )

    # def post(self, request: HttpRequest) -> HttpResponse:
    #     title = "Title Name 222111333"
    #     return render(request, "cards/fragment.html", {
    #         "title": title,
    #     })
