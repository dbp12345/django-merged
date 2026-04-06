from exchange.models import Contacts_Prop
from pwa_crwb.decorators import employee_required

from django.shortcuts import render
from company.models import Employees


@employee_required
def mspa_view(request):
    employee = Employees.objects.get(id=request.session["employee_id"])
    crew = employee.fire_crew

    employees = Employees.objects.filter(fire_crew=crew)

    cards = []
    for e in employees:
        doc = e.get_param_value("MSPA document", Contacts_Prop.TypeChoices.DOCUMENT)
        if not doc:
            continue

        file_url = getattr(doc, "url", doc)

        cards.append({
            "name": e.get_file_as,
            "email": e.get_email,
            "phone": e.get_phone,
            "file_url": file_url,
        })

    context = {
        "employee": employee,
        "cards": cards,
    }

    return render(request, "pwa_crwb/crwb_front/mspa.html", context)
