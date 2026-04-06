import re
import traceback
from collections import defaultdict
from urllib.parse import urlencode

from django.apps import apps
from django.conf import settings
from django.utils.html import format_html
from django.db import transaction
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.db.models.functions import Cast
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.db.models import (
    Prefetch,
    OuterRef,
    Subquery,
    Q,
    Case,
    When,
    CharField,
    TextField,
    DateField,
    DateTimeField,
    IntegerField,
    BooleanField,
    DecimalField,
    FileField,
    FloatField,
)

from company.models import (
    Employees,
    EmergencyContactType,
    DispatchStatus,
    TaskBookType,
    EmployeeType,
    # IdentificationDocumentsType,
    TrainingType,
    Contacts_Prop,
    Tag,
    ContactsExchange,
    DRAWTYPE_CHOICES,
    AVAILABILITY_STATUS,
    INTERACTION_STATUS,
)
from company.models.EmployeesParameters import Employees_Parameters
from company.services.EmployeesService import EmployeesService
from company.utils.filters_emp import apply_all_filters_with_or
from company.utils.trans import trans
from core.models.FieldsSettings import Type
from django.db.models import ForeignKey, OneToOneField, ManyToOneRel


def get_value_suggestions():
    cache_key = "value_suggestions"
    value_suggestions = cache.get(cache_key)

    if value_suggestions is None:
        value_suggestions = {
            "dispatching_status_entries__dispatch_status": [
                status.name for status in DispatchStatus
            ],
            "emergency_contact_entries__type": [
                status.name for status in EmergencyContactType
            ],
            "interaction_entries__type_of_interaction": INTERACTION_STATUS,
            "task_book_entries__type_of_taskbook": [
                status.name for status in TaskBookType
            ],
            "availability_entries__availability_status": AVAILABILITY_STATUS,
            "employees__type": [status.name for status in EmployeeType],
            # "identification_documents_entries__type": [
            #     status.name for status in IdentificationDocumentsType
            # ],
            "student_entries__training_class__course__training_type__name": list(
                TrainingType.objects.values_list("name", flat=True)
            ),
            "employees_parameters_entries__contacts_prop__property_name": list(
                Contacts_Prop.objects.filter()
                .values_list("property_name", flat=True)
                .order_by("property_name")
            ),
            "draws_entries__type": DRAWTYPE_CHOICES,
            "tags": list(Tag.objects.values_list("name", flat=True)),
            "tags__name": list(Tag.objects.values_list("name", flat=True)),
        }
        cache.set(cache_key, value_suggestions, timeout=60 * 60 * 2)  # 2h
    return value_suggestions


def get_relations_params():
    # добавление в колонки
    add = [
        "Created",
        "Created in exc",
        "Fire Crew",
        "Last modified name",
        "Modified time in exc",
        "Updated",
    ]
    grouped = get_cached_grouped_fields_for_relations()
    relations_params = [
        item["name_full"] for group in grouped.values() for item in group
    ]
    relations_params += add

    add_trans = [trans(x) for x in add]
    relations_params_trans = [
        item["name_full_trans"] for group in grouped.values() for item in group
    ]
    relations_params_trans += add_trans
    return relations_params, relations_params_trans


# 2
def get_cached_grouped_fields_for_relations():
    return {}  # для отключения relations таблиц
    cache_key = "grouped_fields_for_relations"
    grouped = cache.get(cache_key)

    if grouped is None:
        EXCLUDED_MODEL = {
            "EmergencyContact",
            "TrainingClass",
            "TrainingType",
            "Course",
            "CrewTimeReport",
            "Evaluation",
            "Crew",
            "Fire",
            "DayOnFire",
            "Employees_Parameters",
            "Employees",
            "FireCrew",
            "Contacts_Prop",
            # "IdentificationDocuments",
            "DriverLicense",
            "Passport",
            "SocialSecurityNumber",
            "MedicalCard",
            # "Student",  # Enabled for custom handling
            "Dispatch",
            "Nomex",
            "Saw",
            "Radio",
            "Truck",
            "Phone",
            "Crew",
            # "FireRun",  # Enabled for custom handling
            "CrewTimeReport",
            "Evaluation",
            "DayOnFire",
            # тут потихоньку буду отключать модели, которые для истории
            "SyncDeliveryLogs",
            "MSPA",
            "CompanyManifest",
            "DrugTest",
            "DispatchingStatus",
            "EmploymentPacket",
            "IQCCard",
            "Interaction",
            "Availability",
            "CurrentAssigned",
            # это сильно скорости не прибавило:
            "TaskBook",
            "Employees_Pictures",
            "NomexCheckIn",
            "NomexCheckOut",
            "Notes",
            "RateOfPay",
            "Draws",
            "Draws",
            "Contracts",
        }

        fields = get_all_filterable_fields_info(Employees, max_depth=5)

        grouped = defaultdict(list)

        for item in fields:
            model = item["model"]
            path = item["path"]
            if model in EXCLUDED_MODEL or path.startswith(
                "identification_documents_entries__"
            ):
                continue

            prefix = path.split("__")[0]
            suffix = "__".join(path.split("__")[1:])

            if suffix == "updated_at":
                continue

            grouped[model].append(
                {
                    "prefix": prefix,
                    "field": suffix,
                    "field_trans": trans(suffix),
                    "type": item["type"],
                    "full": path,
                    "name": item["name"],
                    "name_full": f"{item['name']} {suffix}",
                    "name_full_trans": f"{trans(item['name'])} {trans(suffix)}",
                    "model": model,
                    "app": item["app"],
                }
            )

        # Custom handle IdentificationDocuments
        # Динамическая генерация по типам документов
        # document_fields = [
        #     ("issue_date", "date"),
        #     ("expiration_date", "date"),
        #     ("number", "str"),
        #     ("endorsement", "str"),
        #     ("restriction", "str"),
        # ]

        # тут потихоньку буду отключать модели, которые для истории
        # for doc_type in IdentificationDocumentsType:
        #     prefix = f"identification_documents_entries_{doc_type.name}"
        #     for field_name, field_type in document_fields:
        #         full = f"{prefix}__{field_name}"
        #         grouped["IdentificationDocuments"].append({
        #             "prefix": prefix,
        #             "field": field_name,
        #             "field_trans": trans(field_name),
        #             "type": field_type,
        #             "full": full,
        #             "name": f"Identification Documents {doc_type.name}",
        #             "name_full": f"Identification Documents {doc_type.name} {field_name}",
        #             "name_full_trans": f"{trans('Identification Documents')}
        # {trans(doc_type.name)} {trans(field_name)}",
        #             "model": "IdentificationDocuments",
        #             "app": "company",
        #         })

        # Custom handle TrainingType for Student
        type_fields = [
            ("training_class__date", "date"),
            ("test_score", "str"),
        ]

        for trainingtype in TrainingType.objects.all():
            prefix = f"trainingtype_{trainingtype.id}_entries"
            for field_name, field_type in type_fields:
                full = f"{prefix}__{field_name}"
                grouped["Student"].append(
                    {
                        "prefix": prefix,
                        "field": field_name,
                        "field_trans": trans(field_name),
                        "type": field_type,
                        "full": full,
                        "name": f"Course {trainingtype.name}",
                        "name_full": f"Course {trainingtype.name} {field_name}",
                        "name_full_trans": f"{trans('Course')}{trans(trainingtype.name)} {trans(field_name)}",
                        "model": "Student",
                        "app": "company",
                    }
                )

        # Custom handle FireRun - add fire_run_entries fields to grouped
        # FireRun fields will be automatically included via get_all_filterable_fields_info
        # This ensures FireRun appears in filters similar to Student

        cache.set(cache_key, grouped, timeout=60 * 60 * 2)

    return grouped


def get_cached_grouped_fields():
    fields = get_all_filterable_fields_info(Employees, max_depth=5)
    grouped_raw = group_rel_fields_by_prefix(fields)

    # Add count fields for one-to-many relations (e.g., student_entries__matches_count)
    # These fields allow filtering by count of matching records
    for prefix in list(grouped_raw.keys()):
        # Check if this is a one-to-many relation (has entries suffix or is a reverse relation)
        if prefix.endswith("_entries") or prefix in ["student_entries", "fire_run_entries", "crew_entries"]:
            count_field = {
                "prefix": prefix,
                "prefix_trans": trans(prefix),
                "field": "matches_count",
                "field_trans": trans("matches_count"),
                "type": "str",  # For numeric filtering
                "full": f"{prefix}__matches_count",
                "name": prefix.replace("_entries", "").replace("_", " ").title(),
                "name_full": f"{prefix}__matches_count",
                "name_full_trans": f"{trans(prefix)} {trans('matches_count')}",
                "model": "Employees",
                "app": "company",
            }
            grouped_raw[prefix].append(count_field)

    grouped = {
        key: sorted(value_list, key=lambda x: x["field_trans"])
        for key, value_list in sorted(grouped_raw.items())
    }
    return grouped


def group_rel_fields_by_prefix(rel_fields):
    grouped = defaultdict(list)

    for item in rel_fields:
        path = item["path"]

        parts = path.split("__")
        if len(parts) < 2:
            continue
        prefix = parts[0]
        suffix = "__".join(parts[1:])
        grouped[prefix].append(
            {
                "prefix": prefix,
                "prefix_trans": trans(prefix),
                "field": suffix,
                "field_trans": trans(suffix),
                "type": item["type"],
                "full": path,
                "name": item["name"],
                "name_full": f"{item['name']} {suffix}",
                "name_full_trans": f"{trans(item['name'])} {trans(suffix)}",
                "model": item["model"],
                "app": item["app"],
            }
        )

    return dict(grouped)


def get_all_filterable_fields_info(root_model, max_depth=5):
    cache_key = "all_filterable_fields_info"
    # cache.delete(cache_key)
    fields = cache.get(cache_key)

    if fields is None:
        excluded_substrings = [
            # "employees_parameters_entries",
            "custom_fields",
            "request_to_exchange",
            "request_to_privser",
            "sync_employees",
            "sync_logs_employees",
            "request_from_privser",
            "firecrew_history_entries",
            "entries_as_instructor",
            "emergency_contact_entries_as_relationship",
            "__modified_by",
            # "__id",
            "change_queue_entries",
            "dispatch_entries",
            "nomex_entries",
            "saws_entries",
            "radio_entries",
            "truck_entries",
            "phone_entries",
            "equipment_group",
            "sync_delivery_logs_entries",
            "sync_delivery_logs_employees",
            "vehicle_checkout_entries",
            # тут потихоньку буду отключать модели, которые для истории
            "emergency_contact_entries",
            "nomex_checkin_entries",
            "nomex_checkout_entries",
            "notes_entries",
            "rate_of_pay_entries",
            "draws_entries",
            "employees_pictures_entries",
            "mspa_entries",
            # "MSPA",
            "identification_documents_entries",
            "dl_documents_entries",
            "passport_entries",
            "ssn_entries",
            "medical_card_entries",
            # "IdentificationDocuments",
            "company_manifest_entries",
            # "CompanyManifest",
            "drug_test_entries",
            # "DrugTest",
            "dispatching_status_entries",
            # "DispatchingStatus",
            "employment_packet_entries",
            # "EmploymentPacket",
            "IQC_card_entries",
            # "IQCCard",
            "interaction_entries",
            # "Interaction",
            "availability_entries",
            # "Availability",
            "current_assigned_entries",
            # "CurrentAssigned",
            "crew_entries",
            # "fire_run_entries",  # Enabled for filtering (like student_entries)
            "task_book_entries",
            "__contracts",
            "contracts_as",
            "contacts_prop__property_type",
            "contacts_prop__param_mirror",
            "contacts_prop__property_set_id",
            "contacts_prop__datetime_format",
            "contacts_prop__property_tag",
            "contacts_prop__visibility",
            "sync_updated_at",
            "updated_at",
            # "test",
            "created_in_exchange",
            "employees__type",
            "assigned_to_tickets",
            # "company_workers_as_employees",
            "created_for_tickets",
            "created_tickets",
            "punch_event_set",
            "task_as_employees",
            "tickets_as_employees",
            "user",
            "work_session_set",
        ]

        fields = []

        def get_field_type(field):
            if isinstance(field, (CharField, TextField)):
                return "str"
            elif isinstance(field, DateField) and not isinstance(field, DateTimeField):
                return "date"
            elif isinstance(field, DateTimeField):
                return "datetime"
            elif isinstance(field, IntegerField):
                return "str"
            elif isinstance(field, BooleanField):
                return "str"
            elif isinstance(field, DecimalField):
                return "str"
            elif isinstance(field, FileField):
                return "str"
            return None

        def walk(model, path="", depth=0, visited=None):
            if visited is None:
                visited = set()
            if depth > max_depth or model in visited:
                return
            visited.add(model)
            for field in model._meta.get_fields():
                field_type = get_field_type(field)
                # Прямые фильтруемые поля
                if field_type:
                    full_path = f"{path}__{field.name}" if path else field.name
                    if any(exclude in full_path for exclude in excluded_substrings):
                        continue
                    if depth == 0:
                        fields.append(
                            {
                                "path": f"employees__{full_path}",
                                "type": field_type,
                                "name": model._meta.verbose_name,
                                # "one_to_many": False,
                                # "depth": depth
                                "model": model.__name__,
                                "app": model._meta.app_label,
                            }
                        )
                    else:
                        fields.append(
                            {
                                "path": full_path,
                                "type": field_type,
                                "name": model._meta.verbose_name,
                                # "one_to_many": False,
                                # "depth": depth
                                "model": model.__name__,
                                "app": model._meta.app_label,
                            }
                        )

                # Прямые связи (ForeignKey, OneToOne)
                elif isinstance(field, (ForeignKey, OneToOneField)):
                    related_model = field.related_model
                    new_path = f"{path}__{field.name}" if path else field.name
                    walk(related_model, new_path, depth + 1, visited.copy())

                # Обратные связи (ManyToOneRel)
                elif isinstance(field, ManyToOneRel):
                    related_model = field.related_model
                    related_name = field.get_accessor_name()
                    new_path = f"{path}__{related_name}" if path else related_name
                    walk(related_model, new_path, depth + 1, visited.copy())

        walk(root_model)
        cache.set(cache_key, fields, timeout=60 * 60 * 1)  # 1h
    return fields


def parse_or_filter_groups(request_items):
    group_logic_map = {}
    grouped = {}

    for key, value in request_items:
        logic_match = re.match(r"^f__(\d+)__group_logic$", key)
        if logic_match:
            group_index = int(logic_match.group(1))
            if value in ("and", "or"):
                group_logic_map[group_index] = value
            continue  # не добавлять в grouped

        match = re.match(r"^f__(\d+)_(\d+)__(.+)$", key)
        if match:
            g_index, r_index, field_key = match.groups()
            grouped.setdefault(int(g_index), {}).setdefault(int(r_index), {})[
                field_key
            ] = value

    result = []
    for g_index in sorted(grouped):
        group_rows = grouped[g_index]
        group = []
        for row_data in group_rows.values():
            group.append(
                {
                    "field": row_data.get("field"),
                    "operator": row_data.get("operator"),
                    "value": row_data.get("value", ""),
                    "value_from": row_data.get("value_from", ""),
                    "value_to": row_data.get("value_to", ""),
                }
            )
        result.append(group)

    return result, group_logic_map


def get_relations_rows(employee, field=None):
    # вывод для внешнего вида в таблицу
    from zoneinfo import ZoneInfo

    tz_la = ZoneInfo("America/Los_Angeles")

    FIELD_MAPPER = {}

    grouped = get_cached_grouped_fields_for_relations()
    for group in grouped.values():
        for item in group:
            attr = f"{item['prefix']}_rel"
            subfield = item["field"]
            ftype = item["type"]
            FIELD_MAPPER[item["name_full"]] = (attr, subfield, ftype)

    # Прямая информация
    DIRECT_FIELDS = {
        "Fire Crew": lambda e: e.fire_crew.name if e.fire_crew else "",
        "Last modified name": lambda e: e.last_modified_name,
        "Modified time in exc": lambda e: (
            e.last_modified_time.astimezone(tz_la).strftime("%m/%d/%Y %H:%M")
            if e.last_modified_time
            else ""
        ),
        "Created in exc": lambda e: (
            e.datetime_created.astimezone(tz_la).strftime("%m/%d/%Y %H:%M")
            if e.datetime_created
            else ""
        ),
        "Created": lambda e: (
            e.created_at.astimezone(tz_la).strftime("%m/%d/%Y %H:%M")
            if e.created_at
            else ""
        ),
        "Updated": lambda e: (
            e.updated_at.astimezone(tz_la).strftime("%m/%d/%Y %H:%M")
            if e.updated_at
            else ""
        ),
    }

    if isinstance(field, list):
        relations_params = field
    elif field:
        relations_params = [field]
    else:
        relations_params, relations_params_trans = get_relations_params()

    result = {}

    for param in relations_params:
        if param in DIRECT_FIELDS:
            result[param] = DIRECT_FIELDS[param](employee)
            continue

        if param not in FIELD_MAPPER:
            continue

        attr, subfield, ftype = FIELD_MAPPER[param]
        entries = getattr(employee, attr, None)
        if not entries:
            result[param] = ""
            continue

        entry = entries[0]

        for part in subfield.split("__"):
            entry = getattr(entry, part, None)
            if entry is None:
                break

        if ftype == "datetime":
            value = entry.astimezone(tz_la).strftime("%m/%d/%Y %H:%M") if entry else ""
        elif ftype == "date":
            value = entry.strftime("%m/%d/%Y") if entry else ""
        else:
            value = entry if entry else ""

        result[param] = value

    return result


def get_employees_all_prefetch_related():
    employees_qs = Employees.objects.prefetch_related(
        Prefetch(
            "employees_parameters_entries",
            queryset=Employees_Parameters.objects.select_related("contacts_prop"),
            to_attr="parameters",
        )
    )
    # prefetches = []
    #
    # grouped = get_cached_grouped_fields_for_relations()
    # added_prefixes = set()
    #
    # for field_group in grouped.values():
    #     for item in field_group:
    #         prefix = item["prefix"]
    #         model_name = item["model"]
    #         app = item["app"]
    #
    #         if prefix in added_prefixes:
    #             continue
    #         added_prefixes.add(prefix)
    #
    #         if prefix.startswith("identification_documents_entries_"):
    #             doc_type = prefix.split("identification_documents_entries_")[1]
    #             queryset = IdentificationDocuments.objects.filter(type=doc_type).order_by("-updated_at")
    #             prefetches.append(
    #                 Prefetch(
    #                     "identification_documents_entries",
    #                     queryset=queryset,
    #                     to_attr=f"{prefix}_rel"
    #                 )
    #             )
    #         elif prefix.startswith("trainingtype_") and prefix.endswith("_entries"):
    #             training_type_id = int(prefix.split("_")[1])
    #             queryset = Student.objects.filter(
    #                 training_class__course__training_type__id=training_type_id
    #             ).order_by("-updated_at")
    #             prefetches.append(
    #                 Prefetch(
    #                     "student_entries",
    #                     queryset=queryset,
    #                     to_attr=f"{prefix}_rel"
    #                 )
    #             )
    #         else:
    #             model_class = apps.get_model(app, model_name)
    #             fields = [f.name for f in model_class._meta.get_fields()]
    #             if "updated_at" in fields:
    #                 queryset = model_class.objects.order_by("-updated_at")
    #             else:
    #                 print(f"[!] Model '{model_class.__name__}' has no 'updated_at' field. Loading without ordering.")
    #                 queryset = model_class.objects.all()
    #             prefetches.append(
    #                 Prefetch(
    #                     prefix,
    #                     queryset=queryset,
    #                     to_attr=f"{prefix}_rel"
    #                 )
    #             )
    #
    # employees_qs = employees_qs.prefetch_related(*prefetches)
    return employees_qs


def get_relation_param_to_annotation():
    return {}  # для отключения relations таблиц
    # annotation для запроса в бд
    relation_param_to_annotation = {}

    grouped = get_cached_grouped_fields_for_relations()

    for group in grouped.values():
        for item in group:
            field_type = item["type"]
            alias = item["full"].replace("__", "_")
            model_class = apps.get_model(item["app"], item["model"])

            filters = Q(employee=OuterRef("pk"))
            if item["prefix"].startswith("identification_documents_entries_"):
                doc_type = item["prefix"].split("identification_documents_entries_")[1]
                filters &= Q(type=doc_type)

            if item["prefix"].startswith("trainingtype_") and item["prefix"].endswith(
                "_entries"
            ):
                training_type_id = int(item["prefix"].split("_")[1])
                filters &= Q(training_class__course__training_type__id=training_type_id)

            subquery = Subquery(
                model_class.objects.filter(filters)
                .order_by("-updated_at")
                .values(item["field"])[:1],
                output_field=(
                    DateField()
                    if field_type == "date"
                    else (
                        DateTimeField()
                        if field_type == "datetime"
                        else FloatField() if field_type == "float" else CharField()
                    )
                ),
            )
            relation_param_to_annotation[item["name_full"]] = (alias, subquery)

    return relation_param_to_annotation


def get_order_employees_related(employees_qs, order_column_name, order_dir):
    # order
    manual = {
        "id": "id",
        "Fire Crew": "fire_crew__name",
        "Created": "created_at",
        "Last modified name": "last_modified_name",
        "Modified time in exc": "last_modified_time",
        "Created in exc": "datetime_created",
        "Updated": "updated_at",
    }

    if order_column_name in manual:
        field = manual[order_column_name]
        return employees_qs.order_by(field if order_dir == "desc" else f"-{field}")

    relation_map = get_relation_param_to_annotation()
    if order_column_name in relation_map and relation_map[order_column_name]:
        alias, _ = relation_map[order_column_name]
        return employees_qs.order_by(alias if order_dir == "desc" else f"-{alias}")

    return employees_qs.order_by(
        "sorted_param" if order_dir == "desc" else "-sorted_param"
    )


@method_decorator(staff_member_required, name="dispatch")
class EmployeesTableView(View):
    def get(self, request, *args, **kwargs):

        # for key in [
        #     "grouped_fields_for_relations",
        #     "employees_table_editable_fields",
        #     "all_filterable_fields_info",
        #     "employees_table_not_editable_fields",
        #     "grouped_fields",
        #     "value_suggestions",
        # ]:
        #     cache.delete(key)

        query_string = urlencode(list(request.GET.lists()), doseq=True)
        f_name = request.GET.get("f_name", None)
        url = reverse("employees_table_data")
        type_param = Type.EMPLOYEES_AJAX.name
        title = "Employees"

        all_params = []
        if f_name:
            # mark_safe(
            #     format_html("<li>
            # <a href=\"/admin/company/employees/\"
            # onclick=\"document.getElementById('filter-panel').classList.remove('open');
            # localStorage.setItem('panelOpen', 'false');\"
            # style=\"background-image: none;\">Employees</a></li>")
            # Construct a breadcrumb navigation with filter name if filter is applied
            # title = format_html(
            #     '<li><a href="/admin/company/employees/" '
            #     "onclick=\"document.getElementById('filter-panel').classList.remove('open'); "
            #     "localStorage.setItem('panelOpen', 'false');\">Employees</a></li>"
            #     "<li>{}</li>",
            #     f_name,
            # )
            # title = f", filter: {f_name}"
            title = f_name

            # Тут отключил колонки для сохраненных фильтров
            # saved_filter = Saved_Filter.objects.filter(name=f_name).first()
            # if saved_filter:
            #     all_params = saved_filter.columns_main

        if not all_params:
            all_params = EmployeesService.get_fields_for_employee_table(
                user=request.user, type_param=type_param
            )

        all_columns = ["File As"] + all_params

        if query_string:
            url = f"{url}?{query_string}"

        return render(
            request,
            "admin/employees_table/employees_table.html",
            {
                "url": url,
                "title": title,
                "columns": all_columns,
                "grouped_fields": get_cached_grouped_fields(),
                "value_suggestions": get_value_suggestions(),
                # "not_editable_fields": get_not_editable_fields(),
                "editable_fields": get_editable_fields(),
            },
        )


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(staff_member_required, name="dispatch")
class EmployeesTableData(View):
    def dispatch(self, request, *args, **kwargs):
        type_param = request.GET.get("type", None)
        try:
            draw = int(request.POST.get("draw", 1))
            start = int(request.POST.get("start", 0))  # Сдвиг для пагинации
            length = int(request.POST.get("length", 10))  # Кол-во записей на странице
            # search_value = request.POST.get("search[value]", "").strip()
            order_column_index = int(request.POST.get("order[0][column]", 0))
            order_dir = request.POST.get("order[0][dir]", None)
            # f_name = request.GET.get("f_name", None)

            # ___
            or_filter_groups, group_logic_map = parse_or_filter_groups(
                request.GET.items()
            )

            if not type_param:
                type_param = Type.EMPLOYEES_AJAX.name
            all_params = EmployeesService.get_fields_for_employee_table(
                user=request.user, type_param=type_param
            )

            # if f_name:
            #     saved_filter = Saved_Filter.objects.filter(name=f_name).first()
            #     if saved_filter:
            #         all_params = all_params + saved_filter.columns_main

            relations_params, relations_params_trans = get_relations_params()
            all_columns = ["File As"] + all_params + relations_params

            # Collect all order parameters from request
            order_params = []
            i = 0
            while True:
                column_key = f"order[{i}][column]"
                dir_key = f"order[{i}][dir]"
                if column_key not in request.POST or dir_key not in request.POST:
                    break
                try:
                    column_index = int(request.POST.get(column_key))
                    order_dir_param = request.POST.get(dir_key)
                    if 0 <= column_index < len(all_columns) and order_dir_param:
                        order_params.append((column_index, order_dir_param))
                except (ValueError, IndexError):
                    pass
                i += 1

            # Fallback to single order if no multi-order found
            if not order_params and order_column_index is not None and order_dir is not None:
                order_params = [(order_column_index, order_dir)]

            if order_params:
                from company.models import Employees_Parameters

                relation_param_to_annotation = get_relation_param_to_annotation()
                employees_qs = get_employees_all_prefetch_related()

                order_fields = []
                annotations_to_apply = {}
                param_type_annotations = {}

                # Process each order column (only those that were actually clicked)
                for idx, (column_index, order_dir_param) in enumerate(order_params):
                    order_column_name = all_columns[column_index]

                    # Check if it's a manual field (no annotation needed)
                    manual = {
                        "id": "id",
                        "Fire Crew": "fire_crew__name",
                        "Created": "created_at",
                        "Last modified name": "last_modified_name",
                        "Modified time in exc": "last_modified_time",
                        "Created in exc": "datetime_created",
                        "Updated": "updated_at",
                    }

                    if order_column_name in manual:
                        field = manual[order_column_name]
                        order_fields.append(field if order_dir_param == "desc" else f"-{field}")
                        continue

                    # Check if it's a relation field
                    if (
                        order_column_name in relation_param_to_annotation
                        and relation_param_to_annotation[order_column_name]
                    ):
                        alias, annotation = relation_param_to_annotation[order_column_name]
                        if alias not in annotations_to_apply:
                            annotations_to_apply[alias] = annotation
                        order_fields.append(alias if order_dir_param == "desc" else f"-{alias}")
                        continue

                    # Employees_Parameters field - needs custom annotation
                    if order_column_name == "File As":
                        order_column_name = "surname"
                        # "File As" maps to "surname" which is a manual field
                        order_fields.append("surname" if order_dir_param == "desc" else "-surname")
                        continue

                    # Create unique annotation names only for fields that need them
                    param_type_name = f"param_type_{idx}"
                    annotation_name = f"sorted_param_{idx}"

                    # Get parameter type
                    param_type_subquery = Contacts_Prop.objects.filter(
                        property_name=order_column_name
                    ).values("property_type")[:1]

                    # Subquery for value
                    value_subquery = Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        contacts_prop__property_name=order_column_name,
                    ).values("value")[:1]

                    # Subquery for date
                    value_date_subquery = Employees_Parameters.objects.filter(
                        employee=OuterRef("pk"),
                        contacts_prop__property_name=order_column_name,
                    ).values("value_date")[:1]

                    # Store annotations (will be applied in two steps)
                    param_type_annotations[param_type_name] = Subquery(param_type_subquery)
                    # Store sorted_param definition to apply after param_type
                    annotations_to_apply[annotation_name] = {
                        "param_type_name": param_type_name,
                        "value_subquery": value_subquery,
                        "value_date_subquery": value_date_subquery,
                    }

                    order_fields.append(annotation_name if order_dir_param == "desc" else f"-{annotation_name}")

                # Apply param_type annotations first (needed for Case/When)
                if param_type_annotations:
                    employees_qs = employees_qs.annotate(**param_type_annotations)

                # Separate relation annotations from sorted_param definitions
                relation_annos = {}
                sorted_param_defs = {}
                for key, value in annotations_to_apply.items():
                    if isinstance(value, dict) and "param_type_name" in value:
                        sorted_param_defs[key] = value
                    else:
                        relation_annos[key] = value

                # Apply relation annotations
                if relation_annos:
                    employees_qs = employees_qs.annotate(**relation_annos)

                # Apply sorted_param annotations (can now reference param_type via Q)
                if sorted_param_defs:
                    sorted_annos = {}
                    for annotation_name, annotation_data in sorted_param_defs.items():
                        param_type_name = annotation_data["param_type_name"]
                        sorted_annos[annotation_name] = Case(
                            When(
                                Q(**{param_type_name: "SystemTime"}),
                                then=annotation_data["value_date_subquery"],
                            ),
                            default=annotation_data["value_subquery"],
                            output_field=DateField(),
                        )
                    employees_qs = employees_qs.annotate(**sorted_annos)

                # Apply all order fields
                if order_fields:
                    employees_qs = employees_qs.order_by(*order_fields)

            else:
                # print("order_by", "-updated_at")
                employees_qs = get_employees_all_prefetch_related()
                employees_qs = employees_qs.order_by("-updated_at")

            column_filters = {}
            i = 0
            while True:
                key = f"columns[{i}][search][value]"
                if key not in request.POST:
                    break
                val = (request.POST.get(key, "") or "").strip()
                if val:
                    column_filters[i] = val
                i += 1

            relations_params, relations_params_trans = get_relations_params()
            if column_filters:
                search_filters = Q()
                all_columns = ["File As"] + all_params + relations_params
                relation_map = get_relation_param_to_annotation()

                for col_index, filter_value in column_filters.items():
                    filter_value = (filter_value or "").strip()
                    if col_index >= len(all_columns):
                        continue
                    column_name = all_columns[col_index]
                    print("search_by", column_name)

                    if column_name in [
                        "File As",
                        "Fire Crew",
                        "Created",
                        "Last modified name",
                        "Modified time in exc",
                        "Created in exc",
                        "Updated",
                    ]:
                        if column_name == "Updated":
                            employees_qs = employees_qs.annotate(
                                updated_at_str=Cast("updated_at", output_field=CharField())
                            )
                            search_filters &= Q(updated_at_str__icontains=filter_value)
                        elif column_name == "Created":
                            employees_qs = employees_qs.annotate(
                                created_at_str=Cast("created_at", output_field=CharField())
                            )
                            search_filters &= Q(created_at_str__icontains=filter_value)
                        elif column_name == "Last modified name":
                            search_filters &= Q(last_modified_name__icontains=filter_value)
                        elif column_name == "Modified time in exc":
                            employees_qs = employees_qs.annotate(
                                last_modified_time_str=Cast("created_at", output_field=CharField())
                            )
                            search_filters &= Q(last_modified_time_str__icontains=filter_value)
                        elif column_name == "Created in exc":
                            employees_qs = employees_qs.annotate(
                                datetime_created_str=Cast("datetime_created", output_field=CharField())
                            )
                            search_filters &= Q(datetime_created_str__icontains=filter_value)
                        elif column_name == "Fire Crew":
                            employees_qs = employees_qs.annotate(
                                fire_crew_str=Cast("fire_crew__name", output_field=CharField())
                            )
                            search_filters &= Q(fire_crew_str__icontains=filter_value)
                        elif column_name == "File As":
                            # Search by surname, given_name, middle_name
                            tokens = [
                                t.strip() for t in re.split(r"[,\s]+", filter_value)
                                if t.strip() and len(t.strip()) >= 2
                            ]
                            if tokens:
                                from company.models import Employees_Parameters
                                props = ["surname", "given_name", "middle_name"]
                                for token in tokens:
                                    sub = Employees_Parameters.objects.filter(
                                        contacts_prop__property_name__in=props,
                                        value__icontains=token,
                                    ).values("employee_id")
                                    search_filters &= Q(pk__in=sub)
                    # Search by related tables
                    elif column_name in relation_map:
                        alias, annotation = relation_map[column_name]
                        if alias and annotation:
                            employees_qs = employees_qs.annotate(**{alias: annotation})
                            search_filters &= Q(**{f"{alias}__icontains": filter_value})
                    # Search by tags
                    elif column_name in ("tags", "tags__name"):
                        search_filters &= Q(tags__name__icontains=filter_value)
                    # Search by parameters table
                    else:
                        search_filters &= Q(
                            employees_parameters_entries__contacts_prop__property_name=column_name,
                            employees_parameters_entries__value__icontains=filter_value,
                        )

                employees_qs = employees_qs.filter(search_filters)

            # Custom filters (includes count filters handling)
            employees_qs = apply_all_filters_with_or(
                employees_qs, or_filter_groups, group_logic_map
            )

            relations_params, relations_params_trans = get_relations_params()
            all_columns = ["File As"] + all_params + relations_params

            if request.GET.get("get_sql_query"):
                from django.http import HttpResponse
                return HttpResponse(str(employees_qs.query), content_type="text/plain")

            total_records = Employees.objects.count()
            filtered_records = employees_qs.count()
            employees_qs = employees_qs[start: start + length]

            data = []
            for employee in employees_qs:
                param_dict = {}
                for p in employee.parameters:
                    name = p.contacts_prop.property_name
                    ptype = getattr(p.contacts_prop, "property_type", "") or ""

                    # If Contacts_Prop is Document — show the file (link with filename) from value_file
                    if ptype == Contacts_Prop.TypeChoices.DOCUMENT:
                        if p.value_file:
                            # safe attempt to get URL and filename
                            url = getattr(p.value_file, "url", "") or ""
                            filename = (
                                getattr(p.value_file, "name", "").split("/")[-1]
                                or "file"
                            )
                            param_dict[name] = (
                                format_html(
                                    "<a href='{}' target='_blank' rel='noreferrer noopener'>{}</a>",
                                    url,
                                    filename,
                                )
                                if url
                                else filename
                            )
                        else:
                            param_dict[name] = ""
                    else:
                        param_dict[name] = p.value or ""

                url_edit = reverse(
                    "admin:%s_%s_change"
                    % (Employees._meta.app_label, Employees._meta.model_name),
                    args=[employee.id],
                )
                link_edit = format_html(
                    "<a href='{}' target='_blank' rel='noreferrer noopener'>{}</a>",
                    url_edit,
                    employee.get_file_as or "-",
                )
                row = {
                    "id": employee.id,
                    "File As": link_edit,
                }

                for param in all_params:
                    if param == "students":
                        url = reverse(
                            f"admin:{ContactsExchange._meta.app_label}_{ContactsExchange._meta.model_name}_change",
                            args=[employee.id],
                        )
                        row[param] = format_html(
                            "<a href='{}?inline=students' "
                            "class='js-inline-modal' data-fragment='#student_entries-group'>edit</a>",
                            url,
                        )
                    else:
                        row[param] = param_dict.get(param, "")

                data.append(row)

            relations_params, relations_params_trans = get_relations_params()
            response = {
                "draw": draw,
                "recordsTotal": total_records,
                "recordsFiltered": filtered_records,
                "data": data,
                "not_editable_fields": ["id", "File As", "students"] + relations_params,
            }

            return JsonResponse(response)

        except Exception as e:
            print(traceback.format_exc())
            return JsonResponse({"error": str(e)}, status=500)


def get_not_editable_fields():
    cache_key = "employees_table_not_editable_fields"
    fields = cache.get(cache_key)

    if fields is None:
        not_editable = ["id", "File As", "students"]

        relations_params, _ = get_relations_params()
        not_editable += relations_params

        grouped_fields = get_cached_grouped_fields()
        for fields_group in grouped_fields.values():
            for item in fields_group:
                # full_path = item.get("full", "")
                # Любое поле из связки делаем not editable
                not_editable.append(item["name_full"])

        fields = sorted(set(not_editable))  # Убираем дубли
        cache.set(cache_key, fields, timeout=60 * 60 * 12)  # 12h

    return fields


def get_editable_fields():
    cache_key = "employees_table_editable_fields"
    fields = cache.get(cache_key)

    if fields is None:
        all_fields = EmployeesService.get_all_fields_for_employee_table()
        not_editable_fields = get_not_editable_fields()
        fields = [f for f in all_fields if f not in not_editable_fields]
        cache.set(cache_key, fields, timeout=60 * 60 * 12)  # 12h

    return fields


@csrf_exempt
def update_employee_parameter(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Method not allowed"}, status=405
        )

    from core.tasks import handle_sync_delivery_log_task
    from exchange.models import Contacts_Prop
    from synchronization.models import Sync_Delivery_Logs
    from synchronization.services.SyncDeliveryService import SyncDeliveryService

    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = "django"

    employee_id = request.POST.get("id")
    param_name = request.POST.get("param_name")
    param_value = request.POST.get("param_value")

    try:
        contacts_prop_obj = Contacts_Prop.objects.get(property_name=param_name)
        employee = Employees.objects.get(id=employee_id)
        # employee.last_modified_time = datetime.now().astimezone()
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
            modified_by=username,
        )
        for sync_delivery_log_id in sync_delivery_log_ids:
            if settings.DEBUG:
                handle_sync_delivery_log_task.run(sync_delivery_log_id)
            else:
                transaction.on_commit(
                    lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(
                        sync_id
                    )
                )
                # handle_sync_delivery_log_task.delay(sync_delivery_log_id)

        sync_delivery_log_ids = SyncDeliveryService.add_sync_delivery_log(
            employee=employee,
            changed_parameters=changed_parameters,
            old_parameters=old_parameters,
            target_system=Sync_Delivery_Logs.TargetSystemChoices.EXCHANGE,
            modified_by=username,
        )
        for sync_delivery_log_id in sync_delivery_log_ids:
            if settings.DEBUG:
                handle_sync_delivery_log_task.run(sync_delivery_log_id)
            else:
                transaction.on_commit(
                    lambda sync_id=sync_delivery_log_id: handle_sync_delivery_log_task.delay(
                        sync_id
                    )
                )
                # handle_sync_delivery_log_task.delay(sync_delivery_log_id)

        return JsonResponse({"status": "success"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
