import re

from django.db.models import (
    Count, Sum, Case, When, IntegerField, Q, F, Value, CharField, Subquery, OuterRef
)
from django.db.models.functions import Coalesce, Concat, Trim
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.admin.utils import quote
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from company.models import Employees, DispatchStatus
from company.models import Employees_Parameters


@method_decorator(staff_member_required, name="dispatch")
class FindByCrwbView(View):
    def get(self, request, *args, **kwargs):
        title = "Find by CRWB"

        # boss_id = 23742

        boss_id = request.GET.get("boss")
        crew_boss = None
        rows = []

        if boss_id:
            crew_boss = get_object_or_404(Employees, id=boss_id)

            boss_filter = Q(fire_run_entries__crew__crew_boss=crew_boss)

            fires_annot = Count(
                "fire_run_entries__crew__fire",
                distinct=True,
                filter=boss_filter,
            )

            # В FireRun.operational_periods (IntegerField)
            # Там хранится уже общее число периодов за весь ран. Это проще: берём Sum("fire_run_entries__operational_periods").
            periods_annot_firerun = Coalesce(
                Sum("fire_run_entries__operational_periods", filter=boss_filter),
                0,
            )

            # В DayOnFire.operational_periods (BooleanField)
            # Тут каждый день на пожаре хранится флаг operational_periods=True/False. Если считать по дням, то это фактически COUNT дней, где стоит галочка.
            periods_annot_dof = Coalesce(
                Sum(
                    Case(
                        When(
                            Q(
                                fire_run_entries__crew__crew_boss=crew_boss,
                                fire_run_entries__day_on_fire_entries__operational_periods=True,
                            ),
                            then=1,
                        ),
                        default=0,
                        output_field=IntegerField(),
                    )
                ),
                0,
            )

            # CHANGED: build file_as at DB level to avoid N+1
            surname_sq = Subquery(
                Employees_Parameters.objects.filter(
                    employee_id=OuterRef("pk"),
                    contacts_prop__property_name="surname",
                ).values("value")[:1]
            )
            given_sq = Subquery(
                Employees_Parameters.objects.filter(
                    employee_id=OuterRef("pk"),
                    contacts_prop__property_name="given_name",
                ).values("value")[:1]
            )
            middle_sq = Subquery(
                Employees_Parameters.objects.filter(
                    employee_id=OuterRef("pk"),
                    contacts_prop__property_name="middle_name",
                ).values("value")[:1]
            )

            rest = Trim(
                Concat(
                    Coalesce(F("given_db"), Value("")),
                    Value(" "),
                    Coalesce(F("middle_db"), Value("")),
                )
            )

            qs = (
                Employees.objects
                .filter(is_manifested=True)
                .filter(boss_filter)
                .exclude(pk=crew_boss.pk)
                .annotate(
                    fires=fires_annot,
                    periods_firerun=periods_annot_firerun,
                    periods_dof=periods_annot_dof,
                    # CHANGED: bring name parts
                    surname_db=surname_sq,
                    given_db=given_sq,
                    middle_db=middle_sq,
                )
                .annotate(
                    # CHANGED: final file_as string
                    file_as_db=Case(
                        When(surname_db__isnull=False, then=Concat(F("surname_db"), Value(", "), rest)),
                        default=rest,
                        output_field=CharField(),
                    ),
                    dispatch_status=Subquery(
                        Employees_Parameters.objects.filter(
                            employee=OuterRef("pk"),
                            # contacts_prop__id=45
                            contacts_prop__property_name="Dispatch Call Status"
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
                    availability_status_annotate=Subquery(
                        Employees_Parameters.objects.filter(
                            employee=OuterRef("pk"),
                            # contacts_prop__id=123
                            contacts_prop__property_name="Availability status"
                        ).values("value"),
                        output_field=CharField()
                    ),
                )
                .order_by("-fires", "-periods_firerun", "id")
            )

            def admin_change_url_by_id(emp_id: int) -> str:
                return reverse("admin:company_employees_change", args=[quote(emp_id)])

            rows = [
                {
                    "id": emp.id,
                    "file_as": emp.file_as_db,
                    "fires": emp.fires,
                    "crew": emp.fire_crew.name if emp.fire_crew else "",
                    "status": emp.dispatch_status,
                    "status_color": DispatchStatus.get_color_by_label(emp.dispatch_status) or "white",
                    "job_title": emp.job_title_annotate,
                    "availability_status": emp.availability_status_annotate,
                    "periods_firerun": emp.periods_firerun,
                    "periods_dof": emp.periods_dof,
                    "admin_url": admin_change_url_by_id(emp.id),
                }
                for emp in qs
            ]

        context = {
            "title": title,
            "crew_boss": crew_boss,
            "rows": rows,
        }
        return render(request, "admin/find_by_crwb/find_by_crwb.html", context)


@csrf_exempt
@staff_member_required
def search_crew_bosses(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse([], safe=False, status=200)

    # если есть запятая ИЛИ пробел — используем склейку в БД
    use_concat = bool(re.search(r"[,\s]", q))

    if use_concat:
        # --- аннотируем file_as и email_db через Subquery
        surname_sq = Subquery(
            Employees_Parameters.objects.filter(
                employee_id=OuterRef("pk"),
                contacts_prop__property_name="surname"
            ).values("value")[:1]
        )
        given_sq = Subquery(
            Employees_Parameters.objects.filter(
                employee_id=OuterRef("pk"),
                contacts_prop__property_name="given_name"
            ).values("value")[:1]
        )
        middle_sq = Subquery(
            Employees_Parameters.objects.filter(
                employee_id=OuterRef("pk"),
                contacts_prop__property_name="middle_name"
            ).values("value")[:1]
        )
        email_sq = Subquery(
            Employees_Parameters.objects.filter(
                employee_id=OuterRef("pk"),
                contacts_prop__property_name="email"
            ).values("value")[:1]
        )

        qs = (
            Employees.objects
            # .filter(crew_entries__isnull=False)  # ← включи, если нужны только реальные crew boss’ы
            .annotate(
                surname_db=surname_sq,
                given_db=given_sq,
                middle_db=middle_sq,
                email_db=email_sq,
            )
            .annotate(
                file_as=Case(
                    When(
                        surname_db__isnull=False,
                        then=Concat(
                            F("surname_db"), Value(", "),
                            Coalesce(F("given_db"), Value("")),
                            Value(" "),
                            Coalesce(F("middle_db"), Value("")),
                            output_field=CharField(),
                        )
                    ),
                    default=Concat(
                        Coalesce(F("given_db"), Value("")),
                        Value(" "),
                        Coalesce(F("middle_db"), Value("")),
                        output_field=CharField(),
                    ),
                    output_field=CharField(),
                )
            )
            .filter(Q(file_as__icontains=q) | Q(email_db__icontains=q))
            .distinct()
            .order_by("file_as")[:50]
        )

        results = [{
            "id": str(e.id),
            "label": (e.file_as or e.email_db or "-") + (f" - {e.email_db}" if getattr(e, "email_db", None) else ""),
            "value": (e.file_as or e.email_db or "-") + (f" - {e.email_db}" if getattr(e, "email_db", None) else ""),
        } for e in qs]

    else:
        # --- быстрый поиск без склейки: OR по фамилии/имени/отчеству/email
        qs = (
            Employees.objects
            # .filter(crew_entries__isnull=False)  # ← включи при необходимости
            .filter(
                employees_parameters_entries__contacts_prop__property_name__in=["surname", "given_name", "middle_name", "email"],
                employees_parameters_entries__value__icontains=q,
            )
            .distinct()
            .order_by("id")[:50]
        )

        results = [{
            "id": str(e.id),
            "label": f"{e.get_file_as} - {e.get_email}",
            "value": f"{e.get_file_as} - {e.get_email}",
        } for e in qs]

    return JsonResponse(results, safe=False, status=200)
