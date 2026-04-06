from datetime import datetime
from decimal import Decimal

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from company.models import Employees, Fire, DayOnFire, Crew, FireRun, JobTitle
from dispatch.models import Dispatch
import re
from company.models import Employees_Parameters


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(staff_member_required, name="dispatch")
class DayOnFireView(View):
    def get(self, request):
        dispatches = (
            Dispatch.objects.filter(
                fire__isnull=False,
                # crew__isnull=False,
                # crew__visible=True
            )
            .select_related("fire")  # чтобы не плодить SQL
            .order_by("-updated_at")
        )

        job_title_unum = [(status.name, status.value) for status in JobTitle]
        prepared_dispatches = []

        for dispatch in dispatches:
            # fire = dispatch.fire
            # parts = [str(dispatch)]  # <== вот оно: имя dispatch'а
            # if fire.fire_number:
            #     parts.append(fire.fire_number)
            # if fire.incident_name:
            #     parts.append(fire.incident_name)
            # if dispatch.first_operational_period:
            #     parts.append(dispatch.first_operational_period.strftime("%m/%d/%Y"))
            # label = ", ".join(parts)

            prepared_dispatches.append({"id": dispatch.id, "label": str(dispatch)})

        return render(
            request,
            "admin/DayOnFire/day_on_fire_page.html",
            {
                "title": "Day On fire Service Page",
                "prepared_dispatches": prepared_dispatches,
                "job_title_list": job_title_unum,
                # "today": date.today().strftime("%Y-%m-%d")
            },
        )

    def post(self, request):
        # exit()
        request_username = request.user.username

        dispatch_id = request.POST.get("dispatch")
        # fire_id = request.POST.get("fire_id")
        incident_name = request.POST.get("incident_name")
        fire_number = request.POST.get("fire_number")
        incident_type = request.POST.get("incident_type")
        agency = request.POST.get("agency")
        state = request.POST.get("state")
        activity_code = request.POST.get("activity_code")
        fuel_type = request.POST.get("fuel_type")
        fire_size = request.POST.get("fire_size")
        dispatch_ec_number = request.POST.get("dispatch_ec_number")

        hotline_in_remarks_form = bool(request.POST.get("hotline_in_remarks"))
        operational_periods_form = bool(request.POST.get("operational_periods"))
        document = request.FILES.get("document")

        # Функция склейки даты и времени
        def join_date_time(date_obj, time_str):
            if not time_str:
                return None
            return datetime.strptime(f"{date_obj} {time_str}", "%Y-%m-%d %H:%M")

        employee_id_list = request.POST.getlist("employee_id[]")
        employee_name_list = request.POST.getlist("employee_name[]")
        job_title_list = request.POST.getlist("job_title[]")
        date_list = request.POST.getlist("date[]")
        clock_in_1_list = request.POST.getlist("clock_in_1[]")
        clock_out_1_list = request.POST.getlist("clock_out_1[]")
        clock_in_2_list = request.POST.getlist("clock_in_2[]")
        clock_out_2_list = request.POST.getlist("clock_out_2[]")
        hours_per_day_list = request.POST.getlist("hours_per_day[]")

        for idx, emp_id in enumerate(employee_id_list):
            if not emp_id or not emp_id.strip():
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"Missing employee ID at row {idx + 1}",
                    },
                    status=400,
                )

        rows = []
        for i in range(len(employee_id_list)):
            date_obj = datetime.strptime(date_list[i], "%m/%d/%Y").date()
            clockin1 = join_date_time(date_obj, clock_in_1_list[i])
            clockout1 = join_date_time(date_obj, clock_out_1_list[i])
            clockin2 = join_date_time(date_obj, clock_in_2_list[i])
            clockout2 = join_date_time(date_obj, clock_out_2_list[i])

            rows.append(
                {
                    "date": date_obj,
                    "clockin1": clockin1,
                    "clockout1": clockout1,
                    "clockin2": clockin2,
                    "clockout2": clockout2,
                    "hours_per_day": (
                        Decimal(hours_per_day_list[i])
                        if hours_per_day_list[i]
                        else None
                    ),
                    "employee_id": employee_id_list[i],
                    "employee_name": employee_name_list[i],
                    "job_title": job_title_list[i],
                }
            )

        try:
            dispatch = Dispatch.objects.get(id=dispatch_id)
        except Dispatch.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Missing dispatch"}, status=400
            )

        fire, create_fire = Fire.objects.get_or_create(
            incident_name=incident_name,
            fire_number=fire_number,
            defaults={
                "incident_type": incident_type,
                "agency": agency,
                "state": state,
                "activity_code": activity_code,
                "fuel_type": fuel_type,
                "fire_size": fire_size,
                "modified_by": request_username,
            },
        )

        if not create_fire:
            if activity_code and not fire.activity_code:
                fire.activity_code = activity_code

            if fuel_type and not fire.fuel_type:
                fire.fuel_type = fuel_type

            if fire_size and not fire.fire_size:
                fire.fire_size = fire_size

            if incident_type and not fire.incident_type:
                fire.incident_type = incident_type

            if agency and not fire.agency:
                fire.agency = agency

            if state and not fire.state:
                fire.state = state

            fire.save()

        # def normalize(val):
        #     return val.strip() if val and val.strip() != "" else None
        # try:
        #     fire = Fire.objects.get(id=fire_id)
        #
        #     if (
        #             normalize(fire.incident_name) == normalize(incident_name) and
        #             normalize(fire.fire_number) == normalize(fire_number)
        #     ):
        #         # Всё совпадает, используем существующий
        #         pass
        #     else:
        #         # Есть изменения — создаём новый
        #         fire = Fire.objects.create(
        #             incident_name=incident_name,
        #             fire_number=fire_number,
        #             incident_type=incident_type,
        #             agency=agency,
        #             state=state,
        #             activity_code=activity_code,
        #             fuel_type=fuel_type,
        #             fire_size=fire_size,
        #             modified_by=request_username
        #         )
        # except Fire.DoesNotExist:
        #     # Если по id вообще не найден — создаём новый
        #     fire = Fire.objects.create(
        #         incident_name=incident_name,
        #         fire_number=fire_number,
        #         incident_type=incident_type,
        #         agency=agency,
        #         state=state,
        #         activity_code=activity_code,
        #         fuel_type=fuel_type,
        #         fire_size=fire_size,
        #         modified_by=request_username
        #     )

        crew_boss = None
        crew_name = ""
        if getattr(dispatch, "crew", None):
            crew_boss = getattr(dispatch.crew, "crew_boss", None)
            if crew_boss:
                crew_name = crew_boss.get_file_as

        crew, _ = Crew.objects.get_or_create(
            fire=fire,
            c_number=dispatch_ec_number,
            defaults={
                "crew_name": crew_name,
                "crew_boss": crew_boss,
                "contract": dispatch.contract.number,
                "modified_by": request_username,
            },
        )

        print("rows: ", rows)
        # fire_run_entries = crew.fire_run_entries
        # print("fire_run_entries: ", fire_run_entries)

        for row in rows:
            employee = Employees.objects.get(id=row["employee_id"])

            fire_run, create_fire_run = FireRun.objects.get_or_create(
                crew=crew,
                employee=employee,
                job_title=row["job_title"],
                # Логируем и заполняем из этого employee
                #     firefighter_name = models.CharField(max_length=255, blank=True, null=True)
                #     CRWB_potential = models.CharField(max_length=255, blank=True, null=True)
                #     rating = models.CharField("Rating", max_length=10, blank=True, null=True)
                #     ranking = models.CharField("Ranking", max_length=10, blank=True, null=True)
                #     professionalism_rating = models.CharField(max_length=10, blank=True, null=True)
                #     attitude_rating = models.CharField(max_length=10, blank=True, null=True)
                #     sawyer_rating = models.CharField(max_length=10, blank=True, null=True)
                #     hotline_shifts = models.CharField("Hotline shifts", max_length=255, blank=True, null=True)
                #     start_date = models.DateField("Incident date", blank=True, null=True)
                # Ли говорил, что нам не надо это поле. Но ХЗ, оставлю пока, потому что там есть инфо из импорта
                #     total_shift_tickets = models.IntegerField("Total shift tickets", blank=True, null=True)
                #     operational_periods = models.IntegerField("Operational periods", blank=True, null=True)
                # move to Fire. Need to remove from here
                #     activity_code = models.CharField("Activity code", max_length=25, blank=True, null=True)
                # move to Fire. Need to remove from here
                #     fuel_type = models.CharField("Fuel type", max_length=25, blank=True, null=True)
                # move to Fire. Need to remove from here
                #     fire_size = models.CharField("Fire size", max_length=10, blank=True, null=True)
                #     eval_hotline = models.CharField("Eval hotline", max_length=10, blank=True, null=True)
                #     hotline_in_remarks = models.BooleanField("Hotline in remarks", blank=True, null=True)
                defaults={
                    "hotline_shifts": 1 if hotline_in_remarks_form else 0,
                    "crwb": crew_boss,
                    "operational_periods": 1 if operational_periods_form else 0,
                    "firefighter_name": row["employee_name"],
                    "start_date": row["date"],
                    "modified_by": request_username,
                },
            )

            # print("_____")
            # print("row:", row["date"])
            # print("fire_run.start_date:", fire_run.start_date)

            day, day_created = DayOnFire.objects.update_or_create(
                fire_run=fire_run,
                date=row["date"],
                # crew_time_report=..., #?
                defaults={
                    "clockin1": row["clockin1"],
                    "clockout1": row["clockout1"],
                    "clockin2": row["clockin2"],
                    "clockout2": row["clockout2"],
                    "hours_per_day": row["hours_per_day"],
                    "hotline_in_remarks": hotline_in_remarks_form,
                    "operational_periods": operational_periods_form,
                    "job_title": row["job_title"],
                    "document": document,
                    "modified_by": request_username,
                },
            )

            if not create_fire_run:
                if hotline_in_remarks_form is True:
                    fire_run.hotline_in_remarks = True
                    if day_created:
                        fire_run.hotline_shifts = int(fire_run.hotline_shifts or 0) + 1

                if operational_periods_form is True:
                    if day_created:
                        fire_run.operational_periods = (
                            int(fire_run.operational_periods or 0) + 1
                        )

                if row["date"] < fire_run.start_date:
                    fire_run.start_date = row["date"]

                fire_run.save()

        # for i in range(len(employee_id_list)):
        #     RecordsService.set_operational_periods_for_all_employees(employee_id=employee_id_list[i])

        return JsonResponse(
            {"status": "success"}, safe=False, status=200
        )  # или рендер ошибки


@csrf_exempt
@staff_member_required
def get_crew_employees(request, dispatch_id):
    try:
        dispatch = Dispatch.objects.get(id=dispatch_id)
        crew = dispatch.crew
        fire = dispatch.fire
        # if not crew:
        #     return JsonResponse([], safe=False)

        emp_data = []
        if crew:
            employees = Employees.objects.filter(fire_crew=crew).distinct()
            emp_data = [
                {"id": e.id, "name": e.get_file_as, "job_title": e.get_job_title or ""}
                for e in employees
            ]

        fire_data = {
            "fire_id": fire.id,
            "fire": str(fire),
            "incident_name": fire.incident_name,
            "fire_number": fire.fire_number,
            "dispatch_ec_number": dispatch.ec_number,
            "incident_type": fire.incident_type,
            "agency": fire.agency,
            "state": fire.state,
            "activity_code": fire.activity_code,
            "fuel_type": fire.fuel_type,
            "fire_size": fire.fire_size,
            "reliability_leaving": fire.reliability_leaving,
        }
        return JsonResponse({"emp_data": emp_data, "fire_data": fire_data}, safe=False)

    except Dispatch.DoesNotExist:
        return JsonResponse([], safe=False, status=200)


@csrf_exempt
@staff_member_required
def search_employees(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse([], safe=False, status=200)

    # Разбиваем по запятым/пробелам, убираем короткие токены, ограничиваем количество
    tokens = [t.strip() for t in re.split(r"[,\s]+", q) if t.strip()]
    tokens = [t for t in tokens if len(t) >= 2][:4]

    props = ["surname", "given_name", "middle_name", "email"]

    employees_qs = Employees.objects.filter(is_manifested=True)

    for token in tokens:
        sub = Employees_Parameters.objects.filter(
            contacts_prop__property_name__in=props, value__icontains=token
        ).values_list("employee_id", flat=True)

        employees_qs = employees_qs.filter(Q(pk__in=sub) | Q(email__icontains=token))

    employees = employees_qs.distinct()[:25]

    results = [
        {
            "id": str(e.id),
            "label": f"{e.get_file_as} - {e.get_email}",
            "value": e.get_file_as,
        }
        for e in employees
    ]

    return JsonResponse(results, safe=False, status=200)


# @csrf_exempt
# @staff_member_required
# def search_employees(request):
#     q = request.GET.get("q", "").strip()
#     if not q:
#         return JsonResponse([], safe=False, status=200)

#     employees = Employees.objects.filter(
#         Q(
#             Q(
#                 employees_parameters_entries__contacts_prop__property_name="surname",
#                 employees_parameters_entries__value__icontains=q,
#             )
#             | Q(
#                 employees_parameters_entries__contacts_prop__property_name="given_name",
#                 employees_parameters_entries__value__icontains=q,
#             )
#             | Q(
#                 employees_parameters_entries__contacts_prop__property_name="middle_name",
#                 employees_parameters_entries__value__icontains=q,
#             )
#             | Q(
#                 employees_parameters_entries__contacts_prop__property_name="email",
#                 employees_parameters_entries__value__icontains=q,
#             )
#         ),
#         is_manifested=True,
#     ).distinct()[:25]

#     results = [
#         {
#             "id": str(e.id),
#             "label": f"{e.get_file_as} - {e.get_email}",
#             "value": e.get_file_as,
#         }
#         for e in employees
#     ]

#     return JsonResponse(results, safe=False, status=200)


@csrf_exempt
@staff_member_required
def get_dayonfire_table(request):
    queryset = DayOnFire.objects.select_related(
        "fire_run__crew__fire", "fire_run__employee"
    ).order_by("-id")[:500]

    data = []
    for dof in queryset:
        fire_run = dof.fire_run
        crew = fire_run.crew
        fire = crew.fire if crew else None
        employee = fire_run.employee

        # clockin1 = dof.clockin1.astimezone().strftime("%H:%M") if dof.clockin1 else ""
        # clockout1 = dof.clockout1.astimezone().strftime("%H:%M") if dof.clockout1 else ""
        # clockin2 = dof.clockin2.astimezone().strftime("%H:%M") if dof.clockin2 else ""
        # clockout2 = dof.clockout2.astimezone().strftime("%H:%M") if dof.clockout2 else ""

        data.append(
            {
                "id": dof.id,
                "date": dof.date.strftime("%m/%d/%Y") if dof.date else "",
                "employee": employee.get_file_as if employee else "",
                "job_title": dof.job_title or "",
                # "clock": f"{clockin1}-{clockout1}, {clockin2}-{clockout2}",
                "hours_per_day": (
                    dof.hours_per_day if dof.hours_per_day is not None else ""
                ),
                "hotline_in_remarks": "✔" if dof.hotline_in_remarks else "",
                "operational_periods": "✔" if dof.operational_periods else "",
                "crew": crew.crew_name if crew else "",
                "fire": fire.incident_name if fire else "",
                "fire_number": fire.fire_number if fire else "",
                "incident_type": fire.incident_type if fire else "",
                "agency": fire.agency if fire else "",
                "state": fire.state if fire else "",
                "activity_code": fire.activity_code if fire else "",
                "fuel_type": fire.fuel_type if fire else "",
                "fire_size": fire.fire_size if fire else "",
            }
        )

    return JsonResponse(
        {
            "columns": [
                # {"key": "id", "label": "ID"},
                {"key": "date", "label": "Date"},
                {"key": "employee", "label": "Employee"},
                {"key": "job_title", "label": "Job Title"},
                # {"key": "clock", "label": "Clock"},
                {"key": "hours_per_day", "label": "Hours"},
                {"key": "hotline_in_remarks", "label": "Hotline"},
                {"key": "operational_periods", "label": "Op Periods"},
                {"key": "crew", "label": "Crew"},
                {"key": "fire", "label": "Fire"},
                {"key": "fire_number", "label": "Fire #"},
                {"key": "incident_type", "label": "Type"},
                {"key": "agency", "label": "Agency"},
                {"key": "state", "label": "State"},
                {"key": "activity_code", "label": "Activity code"},
                {"key": "fuel_type", "label": "Fuel type"},
                {"key": "fire_size", "label": "Fire size"},
            ],
            "rows": data,
        }
    )


@csrf_exempt
@staff_member_required
def delete_dayonfire(request, obj_id):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Only POST allowed"}, status=405
        )

    try:
        obj = DayOnFire.objects.get(id=obj_id)
    except DayOnFire.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "DayOnFire not found"}, status=404
        )

    fire_run = obj.fire_run

    if obj.hotline_in_remarks and int(fire_run.hotline_shifts or 0) > 0:
        fire_run.hotline_shifts = int(fire_run.hotline_shifts or 0) - 1

    if obj.operational_periods and int(fire_run.operational_periods or 0) > 0:
        fire_run.operational_periods = int(fire_run.operational_periods or 0) - 1

    fire_run.save()
    obj.delete()
    return JsonResponse({"status": "success"})
