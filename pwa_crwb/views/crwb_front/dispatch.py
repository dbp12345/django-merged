from dispatch.models.Dispatch import Dispatch, Status
from pwa_crwb.decorators import employee_required

from django.shortcuts import render
from company.models import Employees, EmployeeType


@employee_required
def dispatch_view(request):
    employee = Employees.objects.get(id=request.session["employee_id"])

    # crew_employees = Employees.objects.filter(fire_crew=employee.fire_crew)

    dispatches = (
        Dispatch.objects
        .filter(crew=employee.fire_crew, status__in=[Status.ON_FIRE, Status.SCHEDULED])
        .prefetch_related(
            "equipment_group",
            "equipment_group__truck_entries",
            "equipment_group__saws_entries",
            "equipment_group__radio_entries",
            "equipment_group__phone_entries",
        )
        .all()
    )

    dispatch_data = []
    for dispatch in dispatches:
        groups = list(dispatch.equipment_group.all())

        trucks = [item for g in groups for item in g.truck_entries.all()]
        saws = [item for g in groups for item in g.saws_entries.all()]
        radios = [item for g in groups for item in g.radio_entries.all()]
        phones = [item for g in groups for item in g.phone_entries.all()]

        dispatch_data.append({
            "dispatch": dispatch,
            "trucks": trucks,
            "saws": saws,
            "radios": radios,
            "phones": phones,
        })

    list_dispatches_on = False
    # job_title = employee.get_job_title or ""
    # if "crwb" in job_title.lower() or "engb" in job_title.lower():
    #     list_dispatches_on = True
    if employee.type == EmployeeType.CREW_REP.name:
        list_dispatches_on = True

    list_dispatches = (
        Dispatch.objects
        .filter(status__in=[Status.ON_FIRE])
        .select_related("company_rel", "contract", "fire", "crew__crew_boss")
        .all()
        .order_by("-updated_at")
    )

    context = {
        "employee": employee,
        "dispatch_data": dispatch_data,
        "list_dispatches": list_dispatches,
        "list_dispatches_on": list_dispatches_on,
    }

    return render(request, "pwa_crwb/crwb_front/dispatch.html", context)
