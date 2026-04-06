from django.urls import reverse
from django.views import View
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required

from company.models import Employees, FireCrew
from exchange.models import Contacts_Prop


@method_decorator(staff_member_required, name="dispatch")
class CrewMSPAView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        crew_id = request.GET.get("crew")

        if not crew_id:
            return HttpResponse("Missing crew_id", status=400)

        crew = FireCrew.objects.only("id", "name").filter(id=crew_id).first()
        if not crew:
            return HttpResponse("Crew not found", status=404)

        employees = Employees.objects.filter(fire_crew_id=crew.id)

        cards = []
        for e in employees:
            doc = e.get_param_value("MSPA document", Contacts_Prop.TypeChoices.DOCUMENT)
            if not doc:
                continue

            file_url = getattr(doc, "url", doc)

            employee_url = reverse(f"admin:{e._meta.app_label}_{e._meta.model_name}_change", args=[e.pk])
            cards.append({
                "admin_url": employee_url,
                "name": e.get_file_as,
                "email": e.get_email,
                "phone": e.get_phone,
                "file_url": file_url,
            })

        return render(request, "mspa/mspa.html", {"title": crew.name, "cards": cards})
