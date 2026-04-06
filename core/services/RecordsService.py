from django.db.models import Sum, Case, When, Q, Value, IntegerField
from django.db.models.functions import ExtractYear

from company.models import Employees, FireRun
from exchange.models import Contacts_Prop
from synchronization.services.SyncDeliveryService import SyncDeliveryService


class RecordsService:

    @staticmethod
    def set_operational_periods_for_all_employees(employee_id: int = None, employee: Employees = None):
        # CHANGED: allow optional single-employee recalculation
        if employee_id is None and employee is not None:
            employee_id = employee.id

        job_title_mapping = {
            "ENGBT": {
                "fire_days": "Rec(fd) ENGB(T) Fire Days",
                "hotline_fires": "Rec(fd) ENGB(T) Hotline Fires"
            },
            "CRWB": {
                "fire_days": "Rec(fd) CRWB Fire Days",
                "hotline_fires": "Rec(fd) CRWB Hotline Fires"
            },
            "CRWBT": {
                "fire_days": "Rec(fd) CRWB(T) Fire Days",
                "hotline_fires": "Rec(fd) CRWB(T) Hotline Fires"
            },
            "FFT1": {
                "fire_days": "Rec(fd) F1 Fire Days",
                "hotline_fires": "Rec(fd) F1 Hotline Fires"
            },
            "FFT1T": {
                "fire_days": "Rec(fd) F1(T) Fire Days",
                "hotline_fires": "Rec(fd) F1(T) Hotline Fires"
            },
            "FFT2": {
                "fire_days": "Rec(fd) F2 Fire Days",
                "hotline_fires": "Rec(fd) F2 Hotline Fires"
            },
        }

        props_cache = {
            p.property_name: p
            for p in Contacts_Prop.objects.filter(
                property_name__in={name for mapping in job_title_mapping.values() for name in mapping.values()}
            )
        }

        operational_periods = RecordsService.get_operational_periods_for_all_employees(
            employee_id=employee_id  # CHANGED: pass filter if provided
        )

        for op in operational_periods:
            job_title = op.get("job_title")
            mapping = job_title_mapping.get(job_title)
            if not mapping:
                continue

            emp_id = op.get("employee_id")
            employee_instance = Employees.objects.filter(id=emp_id).first()

            if not employee_instance:
                continue

            fire_days_prop = props_cache.get(mapping["fire_days"])
            hotline_prop = props_cache.get(mapping["hotline_fires"])

            if fire_days_prop:
                SyncDeliveryService.do_sync_parameters(
                    employee_instance,
                    fire_days_prop,
                    value=op.get("total_operational_periods"),
                    modified_by="RecordsService",
                    privser=True,
                    exchange=False,
                )
                # Employees_Parameters.objects.update_or_create(
                #     contacts_prop=fire_days_prop,
                #     employee_id=emp_id,
                #     defaults={"value": op.get("total_operational_periods")}
                # )

            if hotline_prop:
                SyncDeliveryService.do_sync_parameters(
                    employee_instance,
                    hotline_prop,
                    value=op.get("total_hotline_fires"),
                    modified_by="RecordsService",
                    privser=True,
                    exchange=False,
                )
                # Employees_Parameters.objects.update_or_create(
                #     contacts_prop=hotline_prop,
                #     employee_id=emp_id,
                #     defaults={"value": op.get("total_hotline_fires")}
                # )

        # Calculate and save year-based operational periods
        RecordsService.set_operational_periods_by_year_for_all_employees(employee_id=employee_id)

        return operational_periods

    @staticmethod
    def get_operational_periods(employee_id: int = None, employee: Employees = None):
        if employee_id is None:
            if employee is not None:
                employee_id = employee.id
            else:
                return None

        return (
            FireRun.objects
            .filter(
                employee_id=employee_id,
                start_date__isnull=False,
                operational_periods__isnull=False
            )
            .aggregate(total=Sum("operational_periods"))["total"]
        )

    @staticmethod
    def get_operational_periods_for_all_employees(employee_id: int = None, employee: Employees = None):
        # CHANGED: optional filter by employee
        if employee_id is None and employee is not None:
            employee_id = employee.id

        base_qs = FireRun.objects.filter(
            employee_id__isnull=False,
            start_date__isnull=False,
            operational_periods__isnull=False
        )
        if employee_id is not None:
            base_qs = base_qs.filter(employee_id=employee_id)

        return list(
            base_qs
            .values("employee_id", "job_title")
            .annotate(
                total_operational_periods=Sum("operational_periods"),
                total_hotline_fires=Sum(
                    Case(
                        When(
                            Q(hotline_in_remarks=True) | Q(eval_hotline="HL"),
                            then=Value(1)
                        ),
                        default=Value(0),
                        output_field=IntegerField()
                    )
                )
            )
        )

    @staticmethod
    def get_operational_periods_by_year_for_all_employees(
        employee_id: int = None, employee: Employees = None, year: int = None
    ):
        """
        Get operational periods grouped by employee_id and year (not by job_title).
        If year is provided, filters by that year. Otherwise returns all years.
        """
        if employee_id is None and employee is not None:
            employee_id = employee.id

        base_qs = FireRun.objects.filter(
            employee_id__isnull=False,
            start_date__isnull=False,
            operational_periods__isnull=False
        )
        if employee_id is not None:
            base_qs = base_qs.filter(employee_id=employee_id)
        if year is not None:
            base_qs = base_qs.filter(start_date__year=year)

        return list(
            base_qs
            .annotate(year=ExtractYear("start_date"))
            .values("employee_id", "year")
            .annotate(
                total_operational_periods=Sum("operational_periods")
            )
        )

    @staticmethod
    def set_operational_periods_by_year_for_all_employees(employee_id: int = None, employee: Employees = None):
        """
        Calculate and save operational periods by year for all employees.
        Supports years 2023, 2024, 2025, and 2026.
        """
        if employee_id is None and employee is not None:
            employee_id = employee.id

        # Hardcoded years as requested
        years = [2023, 2024, 2025, 2026]
        year_param_mapping = {
            2023: "Rec(fd) 2023 Fire Days",
            2024: "Rec(fd) 2024 Fire Days",
            2025: "Rec(fd) 2025 Fire Days",
            2026: "Rec(fd) 2026 Fire Days",
        }

        # Get all required property names
        param_names = list(year_param_mapping.values())
        props_cache = {
            p.property_name: p
            for p in Contacts_Prop.objects.filter(property_name__in=param_names)
        }

        # Get operational periods by year
        operational_periods_by_year = RecordsService.get_operational_periods_by_year_for_all_employees(
            employee_id=employee_id
        )

        # Group by employee_id and year for easier lookup
        employee_year_data = {}
        for op in operational_periods_by_year:
            emp_id = op.get("employee_id")
            year = op.get("year")
            if emp_id and year:
                if emp_id not in employee_year_data:
                    employee_year_data[emp_id] = {}
                employee_year_data[emp_id][year] = op.get("total_operational_periods") or 0

        # If employee_id is specified, ensure it's in the processing list even if no data
        employees_to_process = set(employee_year_data.keys())
        if employee_id is not None:
            employees_to_process.add(employee_id)

        # Process each employee and year
        for emp_id in employees_to_process:
            employee_instance = Employees.objects.filter(id=emp_id).first()
            if not employee_instance:
                continue

            year_data = employee_year_data.get(emp_id, {})

            for year in years:
                param_name = year_param_mapping.get(year)
                if not param_name:
                    continue

                fire_days_prop = props_cache.get(param_name)
                if not fire_days_prop:
                    continue

                # Get the value for this year, default to 0 if not found
                value = year_data.get(year, 0)

                SyncDeliveryService.do_sync_parameters(
                    employee_instance,
                    fire_days_prop,
                    value=value,
                    modified_by="RecordsService",
                    privser=True,
                    exchange=False,
                )

        return operational_periods_by_year
