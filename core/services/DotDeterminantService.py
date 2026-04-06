from dataclasses import dataclass
from enum import Enum

from django.db.models import Sum
from django.db.models.functions import ExtractYear

from company.models import Employees, FireRun, JobTitle


class DotColor(Enum):
    YELLOW = "yellow"
    BLUE = "blue"
    RED = "red"

@dataclass
class DotSeasonResult:
    color: str
    job_title: str| None
    operational_periods: list
    periods_count: int

class DotDeterminantService:

    @staticmethod
    def get_dot_season(employee_id: int = None, employee: Employees = None):
        color = DotColor.YELLOW.value
        job_title = DotDeterminantService.get_last_job_title(employee_id = employee_id, employee = employee)
        operational_periods = DotDeterminantService.get_operational_periods_filtered(employee_id = employee_id, employee = employee)
        periods_count = len(operational_periods)


        # if job_title in (JobTitle.FFT1.value, JobTitle.CRWB.value, JobTitle.ENGB.value):
        job_title = str(job_title or "")
        if any(sub in job_title for sub in (JobTitle.FFT1.value, JobTitle.CRWB.value, JobTitle.ENGB.value)):
            color = DotColor.BLUE.value
        elif periods_count == 0:
            color = DotColor.YELLOW.value
        elif periods_count >= 1:
            color = DotColor.RED.value


        return DotSeasonResult(color, job_title, operational_periods, periods_count)

    @staticmethod
    def get_last_job_title(employee_id: int = None, employee: Employees = None):
        if employee is not None:
            return employee.get_job_title

        if employee_id is not None:
            return Employees.objects.get(id=employee_id).get_job_title

        return None
        # Это чтобы брать job_title из FireRun
        # return (
        #     FireRun.objects
        #     .filter(employee_id=employee_id)
        #     .exclude(job_title__isnull=True)
        #     .exclude(job_title__exact="")
        #     .order_by("-start_date")
        #     .values_list("job_title", flat=True)
        #     .first()
        # )


    @staticmethod
    def get_operational_periods_filtered(employee_id: int = None, employee: Employees = None):
        if employee_id is None:
            if employee is not None:
                employee_id = employee.id
            else:
                return None

        return list(
            FireRun.objects
            .filter(
                employee_id=employee_id,
                start_date__isnull=False,
                operational_periods__isnull=False
            )
            .annotate(year=ExtractYear("start_date"))
            .filter(year__isnull=False)
            .values("year")
            .annotate(total_operational_periods=Sum("operational_periods"))
            .filter(total_operational_periods__gte=15)
            .order_by("year")
        )

