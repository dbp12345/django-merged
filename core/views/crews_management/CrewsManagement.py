import json

from django.db import transaction
from django.db.models import Subquery, OuterRef, BooleanField, CharField, DateField, Prefetch, Q, FilteredRelation, Exists, F
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from company.models import Employees, FireCrew, DispatchStatus, DispatchingStatus, Student, Employees_Parameters, FireRun, TrainingClass
from company.services.EmployeesService import EmployeesService
from company.utils.filters_emp import apply_all_filters_with_or
from company.views.EmployeesParametersAjaxView import get_relation_param_to_annotation, get_employees_all_prefetch_related, get_relations_rows, \
    parse_or_filter_groups
from core import settings
from core.models import Saved_Filter, Saved_Filter_Order
from dispatch.models import Dispatch
from dispatch.models.Contracts import ContractType, Company
from dispatch.models.Dispatch import Status

STATUSES_FOR_CHANGE = [
    (DispatchStatus.AVAILABLE_FOR_DISPATCH.value[0], DispatchStatus.AVAILABLE_FOR_DISPATCH.value[0]),
    (DispatchStatus.ON_FIRE.value[0], DispatchStatus.ON_FIRE.value[0]),
    (DispatchStatus.CHECKED_IN.value[0], DispatchStatus.CHECKED_IN.value[0]),
    (DispatchStatus.ACCEPTED_DISPATCH.value[0], DispatchStatus.ACCEPTED_DISPATCH.value[0]),
    (DispatchStatus.RESTING.value[0], DispatchStatus.RESTING.value[0]),
    (DispatchStatus.NOT_ON_FIRE.value[0], DispatchStatus.NOT_ON_FIRE.value[0]),
    (DispatchStatus.IN_ROUTE.value[0], DispatchStatus.IN_ROUTE.value[0]),
    (DispatchStatus.RNR.value[0], DispatchStatus.RNR.value[0]),
]

FILTERS_COUNT = 4

def get_filters(user):
    saved_order_instance = Saved_Filter_Order.objects.filter(user=user).first()
    if saved_order_instance:
        ids = saved_order_instance.order
        filters_queryset = Saved_Filter.objects.filter(id__in=ids)
        filters_dict = {str(f.id): f for f in filters_queryset}

        ordered_filters = [filters_dict[str(i)] for i in ids if str(i) in filters_dict]

        if len(ordered_filters) < FILTERS_COUNT:
            missing = FILTERS_COUNT - len(ordered_filters)
            extra_filters = list(
                Saved_Filter.objects.exclude(id__in=[int(i) for i in ids])
                .order_by("-id")[:missing]
            )
            ordered_filters.extend(extra_filters)

            if ordered_filters:
                last = ordered_filters[-1]
                while len(ordered_filters) < FILTERS_COUNT:
                    ordered_filters.append(last)

        return ordered_filters[:FILTERS_COUNT]

    base = list(Saved_Filter.objects.order_by("-id")[:FILTERS_COUNT])
    if not base:
        return []
    while len(base) < FILTERS_COUNT:
        base.append(base[-1])
    return base


@method_decorator(staff_member_required, name="dispatch")
class CrewsManagementView(View):
    def get(self, request, *args, **kwargs):
        title = "Crews management"
        filters = get_filters(request.user)
        filters_all = list(Saved_Filter.objects.values("id", "name"))

        groups_qs = list(
            FireCrew.objects
            .filter(visible=True)
            .exclude(group__isnull=True)
            .exclude(group__exact="")
            .values_list("group", flat=True)
            .distinct()
        )

        groups_additional = (
            "On Fire",
            "On Fire Crews",
            "On Fire Engines",
            "Not on Fire",
            "Dust Busters Plus LLC",
            "Idaho Land Services LLC",
            "DBP South LLC",
            "Southern Solutions LLC",
        )
        groups_all = list(groups_additional) + groups_qs

        selected_groups = request.GET.getlist("group")

        dispatch_subquery = Dispatch.objects.filter(
            crew=OuterRef("pk"),
        ).order_by("-updated_at")  # берём самый свежий

        crews = (
            FireCrew.objects.filter(visible=True)
            .only("id", "name", "group")
            .annotate(
                dispatch_id=Subquery(dispatch_subquery.values("id")[:1]),
                dispatch_ec_number=Subquery(dispatch_subquery.values("ec_number")[:1]),
                dispatch_company=Subquery(dispatch_subquery.values("company")[:1]),
                dispatch_status=Subquery(dispatch_subquery.values("status")[:1]),
                # changed: keep contract_type_category in the same latest-dispatch annotation
                dispatch_contract_type_category=Subquery(
                    dispatch_subquery.values("contract__type_category")[:1]
                ),
                dispatch_contract__company_rel__id=Subquery(
                    dispatch_subquery.values("contract__company_rel__id")[:1]
                ),
            )
        )

        crew_id = request.GET.get("crew_id")
        if crew_id:
            crews = crews.filter(id=crew_id)
            selected_groups = None

        if selected_groups:
            selected_groups_set = set(selected_groups)
            # Task:
            # Change
            #  “On Fire Crews” to “On Fire”
            #
            # Add
            # “On Fire Crews”
            # = if on fire and contract category=Crew
            #
            # “On Fire Engines”
            # = if on fire and contract category=Engines
            #
            # “Not on Fire”
            # =not contains on_fire and scheduled
            #
            # Dust Busters Plus LLC
            # = on fire status & company is Dust busters
            #
            # Idaho Land Services
            # = on fire status & company is
            #
            # DBP South LLC
            # = on fire status & company is
            #
            # Souther Solutions LLC
            # = on fire status & company is

            filters_q = Q()
            if "On Fire" in selected_groups_set:
                # это для фильрации если хотябы у одноко пользователя есть статус "On Fire"
                # filters_q |= Q(
                #     employees__employees_parameters_entries__contacts_prop__property_name="Dispatch Call Status",
                #     employees__employees_parameters_entries__value="On Fire"
                # )
                filters_q |= Q(dispatch_status__in=[Status.ON_FIRE, Status.SCHEDULED])
                selected_groups_set.discard("On Fire")
            if "On Fire Crews" in selected_groups_set:
                filters_q |= Q(
                    dispatch_status__in=[Status.ON_FIRE, Status.SCHEDULED],
                    dispatch_contract_type_category=ContractType.CREW
                )
                selected_groups_set.discard("On Fire Crews")
            if "On Fire Engines" in selected_groups_set:
                filters_q |= Q(
                    dispatch_status__in=[Status.ON_FIRE, Status.SCHEDULED],
                    dispatch_contract_type_category=ContractType.ENGINE
                )
                selected_groups_set.discard("On Fire Engines")
            if "Not on Fire" in selected_groups_set:
                filters_q |= ~Q(dispatch_status__in=[Status.ON_FIRE, Status.SCHEDULED]) | Q(dispatch_status__isnull=True)
                selected_groups_set.discard("Not on Fire")
            if "Dust Busters Plus LLC" in selected_groups_set:
                filters_q |= Q(
                    dispatch_status=Status.ON_FIRE,
                    dispatch_contract__company_rel__id=1
                )
                selected_groups_set.discard("Dust Busters Plus LLC")
            if "Idaho Land Services LLC" in selected_groups_set:
                filters_q |= Q(
                    dispatch_status=Status.ON_FIRE,
                    dispatch_contract__company_rel__id=2
                )
                selected_groups_set.discard("Idaho Land Services LLC")
            if "DBP South LLC" in selected_groups_set:
                filters_q |= Q(
                    dispatch_status=Status.ON_FIRE,
                    dispatch_contract__company_rel__id=3
                )
                selected_groups_set.discard("DBP South LLC")
            if "Southern Solutions LLC" in selected_groups_set:
                filters_q |= Q(
                    dispatch_status=Status.ON_FIRE,
                    dispatch_contract__company_rel__id=4
                )
                selected_groups_set.discard("Southern Solutions LLC")

            if selected_groups_set:
                filters_q |= Q(group__in=selected_groups_set)

            # crews = crews.filter(filters_q).distinct()
            crews = crews.filter(filters_q)

        crews = crews.order_by("name")

        # for crew in crews:
        #     print("crew.name: ", crew.name)
        #     for employee in crew.employees.all():
        #         for dispatch_status_entry in employee.dispatching_status_entries.all():
        #             print("dispatch_status: ", dispatch_status_entry.dispatch_status)

        context = {
            "groups": groups_all,
            "selected_groups": selected_groups,
            "filters": filters,
            "filters_all": filters_all,
            "crews": crews,
            "all_crews": FireCrew.objects.filter(visible=True).only("id", "name"),
            "title": title,
            "statuses_for_change": STATUSES_FOR_CHANGE,
            "statuses_for_change_single": STATUSES_FOR_CHANGE,
        }
        return render(request, "admin/crews_management.html", context)


@method_decorator(staff_member_required, name="dispatch")
class CrewsManagementDataView(View):
    def get(self, request, *args, **kwargs):
        from company.views.EmployeesParametersAjaxView import get_relations_params
        filters = get_filters(request.user)
        employees_by_filter = {}
        filter_counts = {}

        relation_map = get_relation_param_to_annotation()

        for filter_obj in filters:
            if not filter_obj:
                continue
            display_fields = filter_obj.columns
            params = filter_obj.params

            employees_qs = (
                get_employees_all_prefetch_related()
                .filter(is_manifested=True, fire_crew__isnull=True)
                .annotate(
                    ne_true=FilteredRelation(
                        "employees_parameters_entries",
                        condition=Q(
                            employees_parameters_entries__contacts_prop_id=197,
                            employees_parameters_entries__value_bool=True,
                        ),
                    )
                )
                .filter(ne_true__isnull=True)
                .order_by("-updated_at")
            )

            # аннотируем только нужные поля
            for field in display_fields:
                if field in relation_map and relation_map[field]:
                    alias, annotation = relation_map[field]
                    employees_qs = employees_qs.annotate(**{alias: annotation})

            or_filter_groups, group_logic_map = parse_or_filter_groups(params.items())

            # Фильтрация по указанному полю
            employees_qs = apply_all_filters_with_or(employees_qs, or_filter_groups, group_logic_map)

            employees_qs = employees_qs.prefetch_related(
                Prefetch(
                    "dispatching_status_entries",  # ← вот правильное имя
                    queryset=DispatchingStatus.objects.order_by("-updated_at"),
                    to_attr="prefetched_dispatch"
                )
            )
            # дорого по ресурсам считать. Перенёс подсчёт на фронт через JS
            # filter_counts[filter_obj.id] = employees_qs.order_by().values("id").count()
            filter_counts[filter_obj.id] = "-"

            employees_by_filter[filter_obj.id] = []
            relations_param_set = get_relations_params()
            for emp in employees_qs:
                param_dict = {p.contacts_prop.property_name: p.value for p in getattr(emp, "parameters", [])}
                # relations_data = get_relations_rows(emp)

                row = {
                    "id": emp.id,
                    "status": emp.get_param_value("Dispatch Call Status"),
                    "status_color": DispatchStatus.get_color_by_label(emp.get_param_value("Dispatch Call Status")) or "White",
                }

                for field in display_fields:
                    if field in relation_map and relation_map[field]:
                        alias, _ = relation_map[field]
                        row[field] = getattr(emp, alias, "")
                    # elif field in relations_data:
                    #     row[field] = relations_data[field]
                    elif field in relations_param_set:
                        relations_data = get_relations_rows(emp, field)
                        row[field] = relations_data[field]
                    elif field in param_dict:
                        row[field] = param_dict[field]
                    elif hasattr(emp, field):
                        row[field] = getattr(emp, field, "")
                    else:
                        row[field] = ""

                employees_by_filter[filter_obj.id].append(row)

        from collections import defaultdict

        employees_qs = (
            Employees.objects
            .select_related("fire_crew")
            .annotate(
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
                # student_class_date=Subquery(
                #     Student.objects.filter(employee=OuterRef("pk"))
                #     .order_by("-updated_at")
                #     .values("training_class__date")[:1],
                #     output_field=DateField()
                # ),
                dispatch_status=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=45
                        contacts_prop__property_name="Dispatch Call Status"
                    ).values("value"),
                    output_field=CharField()
                ),
                mspa_expiration_date=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=26
                        contacts_prop__property_name="MSPA Expiration Date"
                    ).values("value_date"),
                    output_field=DateField()
                ),
                emt_value=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=11
                        contacts_prop__property_name="EMT"
                    ).values("value"),
                    output_field=CharField()
                ),
                job_title_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=123
                        contacts_prop__property_name="job_title"
                    ).values("value"),
                    output_field=CharField()
                ),
                surname_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=128
                        contacts_prop__property_name="surname"
                    ).values("value"),
                    output_field=CharField()
                ),
                given_name_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=140
                        contacts_prop__property_name="given_name"
                    ).values("value"),
                    output_field=CharField()
                ),
                middle_name_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=136
                        contacts_prop__property_name="middle_name"
                    ).values("value"),
                    output_field=CharField()
                ),
                email_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=129
                        contacts_prop__property_name="email"
                    ).values("value"),
                    output_field=CharField()
                ),
                ranking_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=24
                        contacts_prop__property_name="Ranking 1 to 10"
                    ).values("value"),
                    output_field=CharField()
                ),
                rating_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=8
                        contacts_prop__property_name="Rating"
                    ).values("value"),
                    output_field=CharField()
                ),
                dob_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=14
                        contacts_prop__property_name="DOB"
                    ).values("value_date"),
                    output_field=DateField()
                ),
                rec_f1_fire_days_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=162
                        contacts_prop__property_name="Rec(fd) F1 Fire Days"
                    ).values("value"),
                    output_field=CharField()
                ),
                rec_f1_hotline_fires_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=163
                        contacts_prop__property_name="Rec(fd) F1 Hotline Fires"
                    ).values("value"),
                    output_field=CharField()
                ),
                rec_f2_fire_days_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=166
                        contacts_prop__property_name="Rec(fd) F2 Fire Days"
                    ).values("value"),
                    output_field=CharField()
                ),
                rec_f2_hotline_fires_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=167
                        contacts_prop__property_name="Rec(fd) F2 Hotline Fires"
                    ).values("value"),
                    output_field=CharField()
                ),
                rec_f1t_hotline_fires_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=167
                        contacts_prop__property_name="Rec(fd) F1(T) Hotline Fires"
                    ).values("value"),
                    output_field=CharField()
                ),
                rec_f1t_fire_days_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=167
                        contacts_prop__property_name="Rec(fd) F1(T) Fire Days"
                    ).values("value"),
                    output_field=CharField()
                ),
                rec_crwb_hotline_fires_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=167
                        contacts_prop__property_name="Rec(fd) CRWB(T) Hotline Fires"
                    ).values("value"),
                    output_field=CharField()
                ),
                rec_crwb_fire_days_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=167
                        contacts_prop__property_name="Rec(fd) CRWB(T) Fire Days"
                    ).values("value"),
                    output_field=CharField()
                ),
                current_trainee_annotate=Subquery(
                    Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        # contacts_prop__id=198
                        contacts_prop__property_name="Current trainee"
                    ).values("value_bool"),
                    output_field=BooleanField()
                ),
                # current_trainee_annotate=Exists(
                #     Employees_Parameters.objects.filter(
                #         employee=OuterRef("pk"),
                #         contacts_prop_id=198,
                #         value_bool=True,
                #     )
                # )
            )
            .filter(fire_crew__isnull=False, fire_crew__visible=True)
        )

        crew_map = defaultdict(list)
        for emp in employees_qs:
            surname = emp.surname_annotate
            given_name = emp.given_name_annotate
            middle_name = emp.middle_name_annotate
            if surname:
                rest = " ".join(part for part in [given_name, middle_name] if part)
                file_as = f"{surname}, {rest}" if rest else surname
            else:
                file_as = " ".join(part for part in [given_name, middle_name] if part)

            def _to_int(v):
                if isinstance(v, int):
                    return v
                try:
                    return int(str(v).strip())
                except (TypeError, ValueError):
                    return 0

            crew_map[str(emp.fire_crew_id)].append({
                "id": emp.id,
                "one": file_as or emp.email_annotate,
                "two": emp.job_title_annotate,
                "three": emp.s212_class_date.strftime("%m/%d/%Y") if emp.s212_class_date else None,
                "four": emp.mspa_expiration_date.strftime("%m/%d/%Y") if emp.mspa_expiration_date else None,
                "five": emp.emt_value,
                "six": emp.ranking_annotate,
                "seven": emp.rating_annotate,
                "eight": emp.dob_annotate.strftime("%m/%d/%Y") if emp.dob_annotate else None,
                "status": emp.dispatch_status,
                "rec_f1_fire_days": _to_int(emp.rec_f1_fire_days_annotate),
                "rec_f1_hotline_fires": _to_int(emp.rec_f1_hotline_fires_annotate),
                "rec_f1t_hotline_fires": _to_int(emp.rec_f1t_hotline_fires_annotate),
                "rec_f1t_fire_days": _to_int(emp.rec_f1t_fire_days_annotate),
                "rec_f2_fire_days": _to_int(emp.rec_f2_fire_days_annotate),
                "rec_f2_hotline_fires": _to_int(emp.rec_f2_hotline_fires_annotate),
                "rec_crwb_hotline_fires": _to_int(emp.rec_crwb_hotline_fires_annotate),
                "rec_crwb_fire_days": _to_int(emp.rec_crwb_fire_days_annotate),
                "current_trainee": emp.current_trainee_annotate,
                "status_color": DispatchStatus.get_color_by_label(emp.dispatch_status) or "white",
                "is_boss": emp.id == emp.fire_crew.crew_boss_id if emp.fire_crew and emp.fire_crew.crew_boss_id else False,
            })

        # old variant
        # crew_data = {
        #     str(crew.id): {
        #         "name": crew.name,
        #         "employees": crew_map.get(str(crew.id), [])
        #     }
        #     for crew in FireCrew.objects.all()
        # }
        crew_data = {
            crew_id: {
                "employees": crew_employees
            }
            for crew_id, crew_employees in crew_map.items()
        }

        return JsonResponse({
            "employees": employees_by_filter,
            "crews": crew_data,
            "filter_counts": filter_counts
        })


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(staff_member_required, name="dispatch")
class AssignEmployeeToCrewView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        employee_id = data.get("employee_id")
        crew_id = data.get("crew_id")

        try:
            employee = Employees.objects.get(pk=employee_id)
            crew = FireCrew.objects.get(pk=crew_id)
            employee.fire_crew = crew
            employee.save(update_fields=["fire_crew"])
            return CrewsManagementDataView().get(request)
        except (Employees.DoesNotExist, FireCrew.DoesNotExist):
            return JsonResponse({"status": "error", "message": "Employee or Crew not found"}, status=404)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(staff_member_required, name="dispatch")
class RemoveEmployeeFromCrewView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        employee_id = data.get("employee_id")

        try:
            employee = Employees.objects.get(pk=employee_id)
            crew = employee.fire_crew

            # если он был crwb, обнуляем у команды
            if crew and crew.crew_boss_id == employee.id:
                crew.crew_boss = None
                crew.save(update_fields=["crew_boss"])

            employee.fire_crew = None
            employee.save(update_fields=["fire_crew"])

            return CrewsManagementDataView().get(request)
        except Employees.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Employee not found"}, status=404)


class FireRunForEmployeeView(View):
    def post(self, request, *args, **kwargs):
        # try:
        data = json.loads(request.body)
        employee_id = data.get("employee_id")
        if not employee_id:
            return JsonResponse({"status": "error", "message": "Missing employee_id"}, status=400)

        # Fire runs
        fire_runs = (
            FireRun.objects
            .filter(employee_id=employee_id)
            .select_related("crew", "crew__fire")
            .order_by("-start_date")[:10]
        )

        fire_runs_list = []
        for fr in fire_runs:
            fire_runs_list.append({
                "job_title": fr.job_title or "",
                "start_date": fr.start_date.strftime("%m/%d/%Y") if fr.start_date else "",
                "crew_fire_state": fr.crew.fire.state if fr.crew and fr.crew.fire else "",
                "operational_periods": fr.operational_periods or "",
                "crew_fire_incident_name": fr.crew.fire.incident_name if fr.crew and fr.crew.fire else "",
                "crew_crew_name": fr.crew.crew_name if fr.crew else "",
                "eval_hotline": fr.eval_hotline or "",
                "hotline_in_remarks": fr.hotline_in_remarks or "",
                "ranking": fr.ranking or "",
            })

        # Students
        employees_qs = Employees.objects.annotate(
            last_s230_date=Subquery(
                Student.objects.filter(
                    employee=OuterRef("pk"),
                    training_class__course__training_type__name="S-230"
                ).order_by("-training_class__date").values("training_class__date")[:1]
            ),
            last_s290_date=Subquery(
                Student.objects.filter(
                    employee=OuterRef("pk"),
                    training_class__course__training_type__name="S-290"
                ).order_by("-training_class__date").values("training_class__date")[:1]
            ),
            last_s131_date=Subquery(
                Student.objects.filter(
                    employee=OuterRef("pk"),
                    training_class__course__training_type__name="S-131"
                ).order_by("-training_class__date").values("training_class__date")[:1]
            ),
            last_is200_date=Subquery(
                Student.objects.filter(
                    employee=OuterRef("pk"),
                    training_class__course__training_type__name="IS-200"
                ).order_by("-training_class__date").values("training_class__date")[:1]
            ),
            surname_annotate=Subquery(
                Employees_Parameters.objects.filter(
                    employee=OuterRef("pk"),
                    # contacts_prop__id=128
                    contacts_prop__property_name="surname"
                ).values("value"),
                output_field=CharField()
            ),
            given_name_annotate=Subquery(
                Employees_Parameters.objects.filter(
                    employee=OuterRef("pk"),
                    # contacts_prop__id=140
                    contacts_prop__property_name="given_name"
                ).values("value"),
                output_field=CharField()
            ),
            middle_name_annotate=Subquery(
                Employees_Parameters.objects.filter(
                    employee=OuterRef("pk"),
                    # contacts_prop__id=136
                    contacts_prop__property_name="middle_name"
                ).values("value"),
                output_field=CharField()
            ),
            email_annotate=Subquery(
                Employees_Parameters.objects.filter(
                    employee=OuterRef("pk"),
                    # contacts_prop__id=129
                    contacts_prop__property_name="email"
                ).values("value"),
                output_field=CharField()
            ),
            ICA_annotate=Subquery(
                Employees_Parameters.objects.filter(
                    employee=OuterRef("pk"),
                    # contacts_prop__id=129
                    contacts_prop__property_name="ICA Number"
                ).values("value"),
                output_field=CharField()
            ),
            DOB_annotate=Subquery(
                Employees_Parameters.objects.filter(
                    employee=OuterRef("pk"),
                    # contacts_prop__id=129
                    contacts_prop__property_name="DOB"
                ).values("value_date"),
                output_field=CharField()
            ),
        ).get(pk=employee_id)

        students_list = []
        if employees_qs.last_s230_date:
            students_list.append(["S-230:", employees_qs.last_s230_date.strftime("%m/%d/%Y")])
        if employees_qs.last_s290_date:
            students_list.append(["S-290:", employees_qs.last_s290_date.strftime("%m/%d/%Y")])
        if employees_qs.last_s131_date:
            students_list.append(["S-131:", employees_qs.last_s131_date.strftime("%m/%d/%Y")])
        if employees_qs.last_is200_date:
            students_list.append(["IS-200:", employees_qs.last_is200_date.strftime("%m/%d/%Y")])


        info_list = []
        surname = employees_qs.surname_annotate
        given_name = employees_qs.given_name_annotate
        middle_name = employees_qs.middle_name_annotate
        if surname:
            rest = " ".join(part for part in [given_name, middle_name] if part)
            file_as = f"{surname}, {rest}" if rest else surname
        else:
            file_as = " ".join(part for part in [given_name, middle_name] if part)
        if file_as:
            info_list.append(["file_as", file_as or employees_qs.email_annotate])

        if employees_qs.ICA_annotate:
            info_list.append(["ICA Number", employees_qs.ICA_annotate])

        if employees_qs.DOB_annotate:
            info_list.append(["DOB", employees_qs.DOB_annotate.strftime("%m/%d/%Y")])


        return JsonResponse({"status": "ok", "data": {"fire_runs": fire_runs_list, "students": students_list, "info": info_list}})
        #
        # except Exception as e:
        #     return JsonResponse({"status": "error", "message": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(staff_member_required, name="dispatch")
class AssignCrewBossView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        employee_id = data.get("employee_id")
        crew_id = data.get("crew_id")

        try:
            crew = FireCrew.objects.get(pk=crew_id)
            if employee_id is not None:
                employee = Employees.objects.get(pk=employee_id)
                # safety check: работник должен быть в этой команде
                if employee.fire_crew_id != crew.id:
                    return JsonResponse({"status": "error", "message": "Employee not in this crew"}, status=400)
            else:
                employee = None

            crew.crew_boss = employee
            crew.save(update_fields=["crew_boss"])

            return JsonResponse({"status": "success"})

        except (Employees.DoesNotExist, FireCrew.DoesNotExist):
            return JsonResponse({"status": "error", "message": "Employee or Crew not found"}, status=404)


@staff_member_required
def firecrew_visible_disable(request, crew_id):
    if not request.user.is_authenticated:
        return JsonResponse({"errors": "You are not authorized to view this page."}, status=403)

    FireCrew.objects.filter(id=crew_id).update(visible=False)
    return JsonResponse({"status": "ok"})


@csrf_exempt
@staff_member_required
def firecrew_status_change(request, crew_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    from exchange.models import Contacts_Prop
    from core.tasks import handle_sync_delivery_log_task
    from synchronization.models import Sync_Delivery_Logs
    from synchronization.services.SyncDeliveryService import SyncDeliveryService

    param_name = "Dispatch Call Status"

    data = json.loads(request.body)
    param_value = data.get("status")

    if not param_value:
        return JsonResponse({"status": "error", "message": "Missing status"})

    try:
        contacts_prop_obj = Contacts_Prop.objects.get(property_name=param_name)
    except Contacts_Prop.DoesNotExist:
        return JsonResponse({"status": "error", "message": f"Contacts_Prop not found: {param_name}"})

    employees = Employees.objects.filter(fire_crew_id=crew_id)
    username = request.user.username if request.user.is_authenticated else "django"

    for employee in employees:
        try:
            employee.last_modified_name = username
            employee.save()

            employees_service = EmployeesService()
            employees_service.set_contact(employee_obj=employee)

            employees_service.set_contact_parameters(contacts_prop_obj, param_value)

            employees_service.do_update_or_create_contact_parameters(modified_by=username)
            changed_parameters = employees_service.get_all_changed_parameters_obj()
            old_parameters = employees_service.get_old_parameters_obj()

            sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
                employee=employee,
                changed_parameters=changed_parameters,
                old_parameters=old_parameters,
                target_system=Sync_Delivery_Logs.TargetSystemChoices.PRIVSER,
                modified_by=username
            )
            for sync_delivery_log_id in sync_delivery_log_ids:
                if settings.DEBUG:
                    handle_sync_delivery_log_task.run(sync_delivery_log_id)
                else:
                    transaction.on_commit(lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(sync_id))
                    # handle_sync_delivery_log_task.delay(sync_delivery_log_id)

            sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
                employee=employee,
                changed_parameters=changed_parameters,
                old_parameters=old_parameters,
                target_system=Sync_Delivery_Logs.TargetSystemChoices.EXCHANGE,
                modified_by=username
            )
            for sync_delivery_log_id in sync_delivery_log_ids:
                if settings.DEBUG:
                    handle_sync_delivery_log_task.run(sync_delivery_log_id)
                else:
                    transaction.on_commit(lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(sync_id))
                    # handle_sync_delivery_log_task.delay(sync_delivery_log_id)

        except Exception as e:
            continue

    return JsonResponse({"status": "ok"})


@csrf_exempt
@staff_member_required
def employee_param_change(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

    from exchange.models import Contacts_Prop
    from core.tasks import handle_sync_delivery_log_task
    from synchronization.models import Sync_Delivery_Logs
    from synchronization.services.SyncDeliveryService import SyncDeliveryService

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    param_name = data.get("param_name")
    employee_id = data.get("employee_id")
    param_value = data.get("status")

    # print("param_name:", param_name)
    # print("param_value:", param_value)

    try:
        contacts_prop_obj = Contacts_Prop.objects.get(property_name=param_name)
    except Contacts_Prop.DoesNotExist:
        return JsonResponse({"status": "error", "message": f"Contacts_Prop not found: {param_name}"}, status=404)

    try:
        employee = Employees.objects.get(id=employee_id)
    except Employees.DoesNotExist:
        return JsonResponse({"status": "error", "message": f"Employee not found: {employee_id}"}, status=404)

    username = request.user.username if request.user.is_authenticated else "django"

    employee.last_modified_name = username
    employee.save()

    employees_service = EmployeesService()
    employees_service.set_contact(employee_obj=employee)

    employees_service.set_contact_parameters(contacts_prop_obj, param_value)

    employees_service.do_update_or_create_contact_parameters(modified_by=username)
    changed_parameters = employees_service.get_all_changed_parameters_obj()
    old_parameters = employees_service.get_old_parameters_obj()

    sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
        employee=employee,
        changed_parameters=changed_parameters,
        old_parameters=old_parameters,
        target_system=Sync_Delivery_Logs.TargetSystemChoices.PRIVSER,
        modified_by=username
    )
    for sync_delivery_log_id in sync_delivery_log_ids:
        if settings.DEBUG:
            handle_sync_delivery_log_task.run(sync_delivery_log_id)
        else:
            transaction.on_commit(lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(sync_id))

    sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
        employee=employee,
        changed_parameters=changed_parameters,
        old_parameters=old_parameters,
        target_system=Sync_Delivery_Logs.TargetSystemChoices.EXCHANGE,
        modified_by=username
    )
    for sync_delivery_log_id in sync_delivery_log_ids:
        if settings.DEBUG:
            handle_sync_delivery_log_task.run(sync_delivery_log_id)
        else:
            transaction.on_commit(lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(sync_id))

    return JsonResponse({"status": "ok"})
