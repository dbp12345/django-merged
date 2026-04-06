import csv
import os
from datetime import datetime
from io import TextIOWrapper
from pathlib import Path, PureWindowsPath
from typing import Union
from collections import defaultdict

from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.db import connection
from django.utils.timezone import make_aware
from django.conf import settings

from company.models import (
    FireRun,
    Employees,
    Employees_Parameters,
    DayOnFire,
    Crew,
    Fire,
)
from core.models import Import_Dayonfire_Row
from core.models.ImportRow import Status


# Если хочешь другой корень — укажи явно. По умолчанию ожидаем, что ты скопировал
# папку Employees прямо в корень проекта (settings.BASE_DIR / "Employees")
DEFAULT_EMPLOYEES_ROOT = Path(settings.BASE_DIR) / "Employees"


def map_win_path_to_server(
    win_path: str, employees_root: Path = DEFAULT_EMPLOYEES_ROOT
) -> Path:
    """
    Преобразует:
    "Z:\\Employees\\...\\file.pdf" или "Employees\\...\\file.pdf" или "Employees/.../file.pdf"
    в Path(employees_root / ... / file.pdf).
    """
    if not win_path:
        return employees_root

    s = win_path.strip().strip('"')  # trim
    tail = os.path.splitdrive(s)[1].lstrip("\\/")  # убрать диск и лидирующие слэши

    # корректно разбить путь, даже если на Linux остались backslashes
    parts = [p for p in PureWindowsPath(tail).parts if p not in (".", "..")]

    # найти "Employees" (case-insensitive) и взять все части ПОСЛЕ него
    rel_parts = []
    for i, p in enumerate(parts):
        if p.lower() == "employees":
            rel_parts = parts[i + 1:]
            break
    if not rel_parts:
        # If "Employees" is not found, use the entire tail as a relative path
        rel_parts = parts

    return employees_root.joinpath(*rel_parts) if rel_parts else employees_root


class CsvForDayOnFireService:
    def __init__(self):
        self.file = None
        self.rows_processed = 0
        self.rows_skipped = 0
        self.errors = []
        self.file_as_index = {}
        self.param_map = {}

    def set_file(self, uploaded_file: Union[UploadedFile, TextIOWrapper]):
        self.file = uploaded_file

    def import_data(self):
        decoded = self._get_decoded_file()
        reader = csv.DictReader(decoded)

        # рабочая штука. Просто закометрирую чистку таблиц про импорте.!
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {Import_Dayonfire_Row._meta.db_table};")
        # exit()

        rows = []
        for row in reader:
            rows.append(Import_Dayonfire_Row(raw_data=row, status=Status.PENDING.name))

        Import_Dayonfire_Row.objects.bulk_create(rows, batch_size=1000)

        return {
            "status": "ok",
        }

    def handle_data(self):
        self.file_as_index, self.param_map = build_employee_param_index()
        rows = Import_Dayonfire_Row.objects.filter(status=Status.PENDING.name)
        for row in rows:
            # print("row", row.raw_data)

            try:
                # 🔥Fire
                fire_number = (row.raw_data.get("Fire Number") or "").strip()
                incident_type = (row.raw_data.get("Incident Type") or "").strip()
                incident_name = (row.raw_data.get("Incident Name") or "").strip()
                agency = (row.raw_data.get("Agency") or "").strip()
                state = (row.raw_data.get("State") or "").strip()
                activity_code = (row.raw_data.get("Activity Code (WF)") or "").strip()
                fire_instance = self._process_Fire(
                    fire_number=fire_number,
                    incident_type=incident_type,
                    incident_name=incident_name,
                    agency=agency,
                    state=state,
                    activity_code=activity_code,
                )

                # 👥Crew
                crew_name = (row.raw_data.get("Crew Boss") or "").strip()
                c_number = (row.raw_data.get("Crew Number") or "").strip()
                contract = (row.raw_data.get("Contract Number") or "").strip()
                crew_instance = self._process_Crew(
                    crew_name=crew_name,
                    c_number=c_number,
                    contract=contract,
                    fire_instance=fire_instance,
                )

                job_code = (row.raw_data.get("Job Code") or "").strip()
                hotline_in_remarks_row = (
                    (row.raw_data.get("Hotline in Remarks? (Y/N)") or "")
                    .strip()
                    .upper()
                )
                if hotline_in_remarks_row == "Y":
                    hotline_in_remarks_bool = True
                elif hotline_in_remarks_row == "N":
                    hotline_in_remarks_bool = False
                else:
                    hotline_in_remarks_bool = None

                operational_periods = row.raw_data.get("Operational Periods")
                operational_periods = (
                    int(operational_periods.strip())
                    if operational_periods and operational_periods.strip().isdigit()
                    else 0
                )
                if operational_periods > 0:
                    operational_periods_bool = True
                else:
                    operational_periods_bool = False

                # 🚒FireRun
                firefighter_name = (row.raw_data.get("Firefighter Name") or "").strip()
                month_year = (row.raw_data.get("Month/Year") or "").strip()
                start_date = (
                    row.raw_data.get("Start Date") or ""
                ).strip()  # TODO из строки в дату "8/29/2023"
                fire_run_instance = self._process_FireRun(
                    crew_instance=crew_instance,
                    firefighter_name=firefighter_name,
                    month_year=month_year,
                    start_date=start_date,
                    job_code=job_code,
                    hotline_in_remarks=hotline_in_remarks_bool,
                )

                # 📅DayOnFire
                paths = (row.raw_data.get("Paths") or "").strip()
                self._process_DayOnFire(
                    fire_run_instance=fire_run_instance,
                    start_date=start_date,
                    job_code=job_code,
                    hotline_in_remarks_bool=hotline_in_remarks_bool,
                    operational_periods_bool=operational_periods_bool,
                    paths=paths,
                )

                # TODO делать обработку paths
                # self.handle_DayOnFire(
                #     dayonfire_instance=dayonfire_instance,
                #     fire_run_instance=fire_run_instance,
                #     job_code=job_code,
                #     start_date=start_date,
                #     hotline_in_remarks_bool=hotline_in_remarks_bool,
                #     operational_periods_bool=operational_periods_bool,
                #     paths=paths
                # )

                row.status = Status.OK.name
                row.save(update_fields=["status"])
            except Exception as e:
                row.error = str(f"Row {row.id + 1}: {str(e)}")
                row.status = Status.FAILED.name
                row.save(update_fields=["error", "status"])
                # self.errors.append(f"Row {row.id}: {str(e)}")

        # return {
        #     "processed": self.rows_processed,
        #     "skipped": self.rows_skipped,
        #     "errors": self.errors,
        # }

    @staticmethod
    def get_status():
        return {
            "ok": Import_Dayonfire_Row.objects.filter(status=Status.OK.name).count(),
            "failed": Import_Dayonfire_Row.objects.filter(
                status=Status.FAILED.name
            ).count(),
            "pending": Import_Dayonfire_Row.objects.filter(
                status=Status.PENDING.name
            ).count(),
        }

    @staticmethod
    def get_errors():
        return list(
            Import_Dayonfire_Row.objects.filter(status=Status.FAILED.name).values_list(
                "error", flat=True
            )
        )

    def _get_decoded_file(self) -> TextIOWrapper:
        if isinstance(self.file, UploadedFile):
            return TextIOWrapper(self.file.file, encoding="utf-8-sig")
        return self.file

    # 🔥Fire
    def _process_Fire(
        self,
        fire_number,
        incident_type,
        incident_name,
        agency,
        state,
        activity_code,
    ):

        try:
            return Fire.objects.get(
                fire_number=fire_number,
                incident_name=incident_name,
                # incident_type=incident_type,
                # agency=agency,
                # state=state,
                # activity_code=activity_code,
                # fuel_type=fuel_type,
                # fire_size=fire_size,
            )
        except Fire.DoesNotExist:
            raise Exception(
                f"No Fire found for: fire_number: {fire_number} - incident_name: {incident_name}"
            )
        except Fire.MultipleObjectsReturned:
            raise Exception(
                f"Multiple Fire found for: fire_number: {fire_number} - incident_name: {incident_name}"
            )

    # 👥Crew
    def _process_Crew(self, crew_name, c_number, contract, fire_instance: Fire):
        # firefighter_name = crew_name
        # В функцию не выношу, просто это раскопирую везде -=
        # employee_qs = get_employee_by_file_as_from_index(firefighter_name, self.file_as_index, self.param_map)
        #
        # employee = None
        # if len(employee_qs) == 1:
        #     employee = employee_qs[0]
        # else:
        #     last_first = firefighter_name.split(",", 1)
        #     last_name = last_first[0].strip()
        #     if " " in last_name:
        #         firefighter_name_modified = firefighter_name.replace(last_name, last_name.replace(" ", "'"))
        #        employee_qs = get_employee_by_file_as_from_index(
        #            firefighter_name_modified,
        #            self.file_as_index,
        #            self.param_map
        #            )
        #         if len(employee_qs) == 1:
        #             employee = employee_qs[0]
        #
        # if not employee:
        #     logger = logging.getLogger("my_import_csv")
        #     logger.debug(
        #         f"NO crew_boss: {crew_name}\n"
        #     )
        # В функцию не выношу, просто это раскопирую везде =-

        try:
            return Crew.objects.get(
                fire=fire_instance,
                c_number=c_number,
                # contract=contract,
            )
        except Crew.MultipleObjectsReturned:
            raise Exception(
                f"Multiple Crew found for: Fire: {fire_instance.id} CN: {c_number}"
            )
        except Crew.DoesNotExist:
            try:
                return Crew.objects.get(
                    fire=fire_instance,
                    # c_number=c_number,
                    # contract=contract,
                )
            except Crew.MultipleObjectsReturned:
                raise Exception(f"Multiple Crew found for: Fire: {fire_instance.id}")
            except Crew.DoesNotExist:
                raise Exception(f"No Crew found for: Fire: {fire_instance.id}")

    # 🚒FireRun
    def _process_FireRun(
        self,
        crew_instance,
        firefighter_name,
        month_year,
        start_date,
        job_code,
        hotline_in_remarks,
    ):
        # В функцию не выношу, просто это раскопирую везде -=
        employee_qs = get_employee_by_file_as_from_index(
            firefighter_name, self.file_as_index, self.param_map
        )

        employee = None
        if len(employee_qs) == 1:
            employee = employee_qs[0]
        else:
            last_first = firefighter_name.split(",", 1)
            last_name = last_first[0].strip()
            if " " in last_name:
                firefighter_name_modified = firefighter_name.replace(
                    last_name, last_name.replace(" ", "'")
                )
                employee_qs = get_employee_by_file_as_from_index(
                    firefighter_name_modified, self.file_as_index, self.param_map
                )
                if len(employee_qs) == 1:
                    employee = employee_qs[0]
                elif len(employee_qs) == 0:
                    raise Exception(f"No employee found for: {firefighter_name}")
                elif len(employee_qs) > 1:
                    raise Exception(f"Multiple employees found for: {firefighter_name}")
        # В функцию не выношу, просто это раскопирую везде =-

        # parsed_datetime = datetime.strptime(start_date, "%m/%d/%Y")

        try:
            return FireRun.objects.get(
                employee=employee,
                crew=crew_instance,
                # start_date=make_aware(parsed_datetime),
                job_title=job_code,
                # hotline_in_remarks=hotline_in_remarks,
            )
        except FireRun.DoesNotExist:
            raise Exception(f"No FireRun found for: {firefighter_name} - {start_date}")
        except FireRun.MultipleObjectsReturned:
            raise Exception(
                f"Multiple FireRun found for: {firefighter_name} - {start_date}"
            )

    # 📅DayOnFire
    def _process_DayOnFire(
        self,
        fire_run_instance,
        start_date,
        job_code,
        hotline_in_remarks_bool,
        operational_periods_bool,
        paths,
    ):
        print("paths:", paths)

        parsed_datetime = datetime.strptime(start_date, "%m/%d/%Y")

        try:
            dayonfire_instance = DayOnFire.objects.get(
                fire_run=fire_run_instance,
                date=make_aware(parsed_datetime),
            )
            if dayonfire_instance.document:
                raise Exception(
                    f"DayOnFire:{dayonfire_instance.id} already contains a document"
                )
        except DayOnFire.DoesNotExist:
            dayonfire_instance = DayOnFire.objects.create(
                fire_run=fire_run_instance,
                job_title=job_code,
                date=make_aware(parsed_datetime),
                hotline_in_remarks=hotline_in_remarks_bool,
                operational_periods=operational_periods_bool,
                # document=filename,
                modified_by="CsvForDayOnFireService",
            )
        except DayOnFire.MultipleObjectsReturned:
            raise Exception(
                f"Multiple DayOnFire for: FireRun: {fire_run_instance.id} - {start_date}"
            )

        # now attach file (common path for both existing-without-file and newly-created)
        server_path = map_win_path_to_server(paths, DEFAULT_EMPLOYEES_ROOT)
        if not server_path.exists():
            raise Exception(f"File not found on server: {server_path}")
            return False, f"Файл не найден на сервере: {server_path}"
        if server_path.is_dir():
            raise Exception(f"Expecting a file, but it's a folder: {server_path}")
            return False, f"Ожидается файл, но это папка: {server_path}"

        filename = server_path.name
        try:
            with server_path.open("rb") as fh:
                django_file = File(fh)
                # model_directory_path (your upload_to) will be applied by Django
                dayonfire_instance.document.save(filename, django_file, save=True)
            return dayonfire_instance
            return True, f"Saved -> {dayonfire_instance.document.name}"
        except Exception as e:
            return dayonfire_instance
            return False, f"Saved failed {server_path}: {e}"

            # raise Exception(f"No DayOnFire for: FireRun: {fire_run_instance.id} - {start_date}")


def build_employee_param_index():
    employee_params = Employees_Parameters.objects.select_related(
        "contacts_prop", "employee"
    ).filter(
        contacts_prop__property_name__in=[
            "file_as",
            "surname",
            "given_name",
            "middle_name",
        ]
    )

    file_as_index = defaultdict(list)  # file_as → [Employees]
    param_map = defaultdict(lambda: defaultdict(str))

    for param in employee_params:
        emp = param.employee
        param_name = param.contacts_prop.property_name
        param_value = (param.value or "").strip()

        param_map[emp.id][param_name] = param_value

        if param_name == "file_as":
            file_as_index[param_value].append(emp)

    return file_as_index, param_map


def get_employee_by_file_as_from_index(
    file_as: str, file_as_index: dict, param_map: dict
):
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
