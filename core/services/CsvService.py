import csv
from datetime import datetime
from io import TextIOWrapper
from typing import Union
from django.core.files.uploadedfile import UploadedFile
from django.db import connection
from django.utils.timezone import make_aware

from company.models import Fire, Crew, FireRun, Employees, Employees_Parameters, DayOnFire
from core.models import Import_Row
from core.models.ImportRow import Status
import logging


class CsvService:
    def __init__(self):
        self.file = None
        self.rows_processed = 0
        self.rows_skipped = 0
        self.errors = []
        self.file_as_index = {}
        self.param_map = {}

    def set_file(self, uploaded_file: Union[UploadedFile, TextIOWrapper]):
        self.file = uploaded_file

    # def import_data2(self):
    #     decoded = self._get_decoded_file()
    #     reader = csv.DictReader(decoded)
    #     with connection.cursor() as cursor:
    #         cursor.execute(f"TRUNCATE TABLE {Import_Row._meta.db_table};")
    #
    #     for row_num, row in enumerate(reader, start=1):
    #         Import_Row.objects.create(
    #             raw_data=row,
    #             status=Status.PENDING.name
    #         )
    #
    #     return {
    #         "status": "ok",
    #     }

    def import_data(self):
        decoded = self._get_decoded_file()
        reader = csv.DictReader(decoded)

        # рабочая штука. Просто закометрирую чистку таблиц про импорте.!
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {Import_Row._meta.db_table};")
            # cursor.execute(f"DELETE FROM {DayOnFire._meta.db_table};")
            # cursor.execute(f"DELETE FROM {FireRun._meta.db_table};")
            # cursor.execute(f"DELETE FROM {Crew._meta.db_table};")
            # cursor.execute(f"DELETE FROM {Fire._meta.db_table};")
        # exit()

        rows = []
        for row in reader:
            rows.append(Import_Row(
                raw_data=row,
                status=Status.PENDING.name
            ))

        Import_Row.objects.bulk_create(rows, batch_size=1000)

        return {
            "status": "ok",
        }

    def handle_data(self):
        self.file_as_index, self.param_map = build_employee_param_index()
        rows = Import_Row.objects.filter(status=Status.PENDING.name)
        for row in rows:
            print("row", row.raw_data)
            try:
                # 🔥Fire
                fire_number = (row.raw_data.get("Fire Number") or "").strip()
                incident_type = (row.raw_data.get("Incident Type") or "").strip()
                incident_name = (row.raw_data.get("Incident Name") or "").strip()
                agency = (row.raw_data.get("Agency") or "").strip()
                state = (row.raw_data.get("State") or "").strip()
                activity_code = (row.raw_data.get("Activity Code (WF)") or "").strip()
                fuel_type = (row.raw_data.get("Fuel Type 1-4") or "").strip()
                fire_size = (row.raw_data.get("Fire Size A, B, C, D, E, F, G") or "").strip()
                fire_instance, _ = self._process_Fire(
                    fire_number,
                    incident_type,
                    incident_name,
                    agency,
                    state,
                    activity_code,
                    fuel_type,
                    fire_size,
                )

                # 👥Crew
                crew_name = (row.raw_data.get("Crew Boss") or "").strip()
                c_number = (row.raw_data.get("Crew Number") or "").strip()
                contract = (row.raw_data.get("Contract Number") or "").strip()
                crew_instance, _ = self._process_Crew(
                    crew_name=crew_name,
                    c_number=c_number,
                    contract=contract,
                    fire_instance=fire_instance
                )

                # 🚒FireRun
                firefighter_name = (row.raw_data.get("Firefighter Name") or "").strip()
                crwb_potential = ""  # not used
                rating = (row.raw_data.get("Rating") or "").strip()
                ranking = (row.raw_data.get("Ranking") or "").strip()
                professionalism_rating = ""  # not used
                attitude_rating = ""  # not used
                sawyer_rating = ""  # not used
                month_year = (row.raw_data.get("Month/Year") or "").strip()
                hotline_shifts = (row.raw_data.get("Hotline Shifts") or "").strip()
                start_date = (row.raw_data.get("Start Date") or "").strip()  # TODO из строки в дату "8/29/2023"
                job_code = (row.raw_data.get("Job Code") or "").strip()
                operational_periods = (row.raw_data.get("Operational Periods") or "").strip()
                total_shift_tickets = (row.raw_data.get("Total Shift Tickets") or "").strip()
                eval_hotline = (row.raw_data.get("Eval Hotline? (B/LC/HL/NA)") or "").strip()
                hotline_in_remarks_row = (row.raw_data.get("Hotline in Remarks? (Y/N)") or "").strip().upper()
                if hotline_in_remarks_row == "Y":
                    hotline_in_remarks_bool = True
                elif hotline_in_remarks_row == "N":
                    hotline_in_remarks_bool = False
                else:
                    hotline_in_remarks_bool = None
                fire_run_instance, _ = self._process_FireRun(
                    firefighter_name=firefighter_name,
                    crwb_potential=crwb_potential,
                    rating=rating,
                    ranking=ranking,
                    professionalism_rating=professionalism_rating,
                    attitude_rating=attitude_rating,
                    sawyer_rating=sawyer_rating,
                    month_year=month_year,
                    hotline_shifts=hotline_shifts,
                    start_date=start_date,
                    job_code=job_code,
                    operational_periods=operational_periods,
                    total_shift_tickets=total_shift_tickets,
                    activity_code=activity_code,
                    fuel_type=fuel_type,
                    fire_size=fire_size,
                    eval_hotline=eval_hotline,
                    hotline_in_remarks=hotline_in_remarks_bool,
                    crew_instance=crew_instance
                )
                # 📅DayOnFire
                # 📝Evaluation
                row.status = Status.OK.name
                row.save(update_fields=["status"])
                # self.rows_processed += 1
            except Exception as e:
                row.error = str(f"Row {row.id + 1}: {str(e)}")
                row.status = Status.FAILED.name
                row.save(update_fields=["error", "status"])
                # self.rows_skipped += 1
                # self.errors.append(f"Row {row.id}: {str(e)}")

        # return {
        #     "processed": self.rows_processed,
        #     "skipped": self.rows_skipped,
        #     "errors": self.errors,
        # }

    @staticmethod
    def get_status():
        return {
            "ok": Import_Row.objects.filter(status=Status.OK.name).count(),
            "failed": Import_Row.objects.filter(status=Status.FAILED.name).count(),
            "pending": Import_Row.objects.filter(status=Status.PENDING.name).count(),
        }

    @staticmethod
    def get_errors():
        return list(Import_Row.objects.filter(status=Status.FAILED.name).values_list("error", flat=True))

    def _get_decoded_file(self) -> TextIOWrapper:
        if isinstance(self.file, UploadedFile):
            return TextIOWrapper(self.file.file, encoding="utf-8-sig")
        return self.file

    # 🔥Fire
    def _process_Fire(self, fire_number, incident_type, incident_name, agency, state, activity_code, fuel_type, fire_size):
        return Fire.objects.get_or_create(
            fire_number=fire_number,
            incident_name=incident_name,
            defaults={
                "incident_type": incident_type,
                "agency": agency,
                "state": state,
                "activity_code": activity_code,
                "fuel_type": fuel_type,
                "fire_size": fire_size,
                # "reliability_leaving": None,
            }
        )

    # 👥Crew
    def _process_Crew(self, crew_name, c_number, contract, fire_instance: Fire):
        firefighter_name = crew_name
        # В функцию не выношу, просто это раскопирую везде -=
        employee_qs = get_employee_by_file_as_from_index(firefighter_name, self.file_as_index, self.param_map)

        employee = None
        if len(employee_qs) == 1:
            employee = employee_qs[0]
        else:
            last_first = firefighter_name.split(",", 1)
            last_name = last_first[0].strip()
            if " " in last_name:
                firefighter_name_modified = firefighter_name.replace(last_name, last_name.replace(" ", "'"))
                employee_qs = get_employee_by_file_as_from_index(firefighter_name_modified, self.file_as_index, self.param_map)
                if len(employee_qs) == 1:
                    employee = employee_qs[0]

        if not employee:
            logger = logging.getLogger("my_import_csv")
            logger.debug(
                f"NO crew_boss: {crew_name}\n"
            )
        # В функцию не выношу, просто это раскопирую везде =-

        crew = Crew.objects.get_or_create(
            fire=fire_instance,
            c_number=c_number,
            defaults={
                "crew_name": crew_name,
                "crew_boss": employee,
                "contract": contract,
            }
        )
        return crew

    # 🚒FireRun
    def _process_FireRun(
            self,
            firefighter_name,
            crwb_potential,
            rating,
            ranking,
            professionalism_rating,
            attitude_rating,
            sawyer_rating,
            month_year,
            hotline_shifts,
            start_date,
            job_code,
            operational_periods,
            total_shift_tickets,
            activity_code,
            fuel_type,
            fire_size,
            eval_hotline,
            hotline_in_remarks,
            crew_instance: Crew
    ):
        # В функцию не выношу, просто это раскопирую везде -=
        employee_qs = get_employee_by_file_as_from_index(firefighter_name, self.file_as_index, self.param_map)

        employee = None
        if len(employee_qs) == 1:
            employee = employee_qs[0]
        else:
            last_first = firefighter_name.split(",", 1)
            last_name = last_first[0].strip()
            if " " in last_name:
                firefighter_name_modified = firefighter_name.replace(last_name, last_name.replace(" ", "'"))
                employee_qs = get_employee_by_file_as_from_index(firefighter_name_modified, self.file_as_index, self.param_map)
                if len(employee_qs) == 1:
                    employee = employee_qs[0]
                elif len(employee_qs) == 0:
                    raise Exception(f"No employee found for: {firefighter_name}")
                elif len(employee_qs) > 1:
                    raise Exception(f"Multiple employees found for: {firefighter_name}")
        # В функцию не выношу, просто это раскопирую везде =-

        operational_periods = int(operational_periods.strip()) if operational_periods and operational_periods.strip().isdigit() else 0
        total_shift_tickets = int(total_shift_tickets.strip()) if total_shift_tickets and total_shift_tickets.strip().isdigit() else 0

        parsed_datetime = datetime.strptime(start_date, "%m/%d/%Y")
        start_date = make_aware(parsed_datetime)

        return FireRun.objects.get_or_create(
            crew=crew_instance,
            employee=employee,
            job_title=job_code,
            defaults={
                "firefighter_name": firefighter_name,
                "CRWB_potential": crwb_potential,
                "rating": rating,
                "ranking": ranking,
                "professionalism_rating": professionalism_rating,
                "attitude_rating": attitude_rating,
                "sawyer_rating": sawyer_rating,
                "month_year": month_year,
                "start_date": start_date,
                "hotline_shifts": hotline_shifts,
                "activity_code": activity_code,
                "fuel_type": fuel_type,
                "fire_size": fire_size,
                "eval_hotline": eval_hotline,
                "hotline_in_remarks": hotline_in_remarks,
                "operational_periods": operational_periods,
                "total_shift_tickets": total_shift_tickets,
            }
        )

    # 📅DayOnFire
    def _process_DayOnFire(self, row: dict, fire_run: FireRun):
        return DayOnFire.objects.get_or_create(
            # fire_run = fire_run
            # crew_time_report =
            # job_title =
            # clockin1 =
            # clockout1 =
            # clockin2 =
            # clockout2 =
            # hours_per_day =
            # document =
            # job_title =
            # total_shift_tickets =
            # operational_periods =
        )


from collections import defaultdict


def build_employee_param_index():
    employee_params = (
        Employees_Parameters.objects
        .select_related("contacts_prop", "employee")
        .filter(contacts_prop__property_name__in=[
            "file_as", "surname", "given_name", "middle_name"
        ])
    )

    file_as_index = defaultdict(list)  # file_as → [Employees]
    param_map = defaultdict(lambda: defaultdict(str))  # emp_id → {param_name: value}

    for param in employee_params:
        emp = param.employee
        param_name = param.contacts_prop.property_name
        param_value = (param.value or "").strip()

        param_map[emp.id][param_name] = param_value

        if param_name == "file_as":
            file_as_index[param_value].append(emp)

    return file_as_index, param_map


def get_employee_by_file_as_from_index(file_as: str, file_as_index: dict, param_map: dict):
    # logger = logging.getLogger("my_import_csv")
    file_as = file_as.strip()
    employees = file_as_index.get(file_as, [])

    if len(employees) == 1:
        # logger.debug(f"[file_as match] '{file_as}' → {employees[0].id}")
        return employees

    # logger.debug(f"[file_as fuzzy fallback] '{file_as}' → {len(employees)} matches, using fuzzy")
    return find_employee_by_file_as_fuzzy_from_index(file_as, param_map)


def find_employee_by_file_as_fuzzy_from_index(file_as: str, param_map: dict):
    # logger = logging.getLogger("my_import_csv")
    file_as = file_as.strip()
    if "," not in file_as:
        # logger.debug(f"[fuzzy fail] '{file_as}' — no comma, cannot parse")
        return []

    last_name, rest = [p.strip() for p in file_as.split(",", 1)]
    parts = rest.split()

    if len(parts) == 2:
        variants = [
            {"first": parts[0], "middle": parts[1]},
            {"first": parts[1], "middle": parts[0]},
        ]
    elif len(parts) == 1:
        variants = [{"first": parts[0], "middle": None}]
    else:
        # logger.debug(f"[fuzzy fail] '{file_as}' — too many name parts")
        return []

    matched_ids = []

    for emp_id, param_dict in param_map.items():
        for v in variants:
            if (
                    param_dict.get("surname", "").lower() == last_name.lower()
                    and param_dict.get("given_name", "").lower() == v["first"].lower()
            ):
                middle_match = True
                if v["middle"] is not None:
                    middle_match = (
                            param_dict.get("middle_name", "").lower() == v["middle"].lower()
                    )
                else:
                    middle_match = (
                            "middle_name" not in param_dict or not param_dict["middle_name"]
                    )

                if middle_match:
                    matched_ids.append(emp_id)

    if matched_ids:
        # logger.debug(f"[fuzzy match] '{file_as}' → {matched_ids}")
        return list(Employees.objects.filter(id__in=matched_ids))

    # logger.debug(f"[fuzzy miss] '{file_as}' → no match found")
    return []
