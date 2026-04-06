from django.utils.timezone import make_aware
from datetime import datetime, date, timedelta
from django.db.models import Q, Subquery, OuterRef
from company.models import *

from company.models import Employees_Parameters, IdentificationDocumentsType
from exchange.models import Contacts_Prop


def apply_all_filters_with_or(employees_qs, or_filter_groups):
    print("or_filter_groups", or_filter_groups)
    if not or_filter_groups:
        return employees_qs

    or_query = Q()

    for group in or_filter_groups:
        and_query = Q()

        for filter_dict in group:
            field = filter_dict.get("field")
            ftype = filter_dict.get("type")
            operator = filter_dict.get("operator")
            value = filter_dict.get("value")
            from_val = filter_dict.get("value_from")
            to_val = filter_dict.get("value_to")

            if not field or not operator:
                continue

            if ftype == "str":
                filtered = apply_employee_filters_all_str(
                    employees_qs, field, value, operator
                )
            elif ftype == "date":
                if operator in ["range"]:
                    filtered = apply_employee_filters_all_date(
                        employees_qs, field, from_val, to_val, operator
                    )
                elif operator in ["more", "less"]:
                    filtered = apply_employee_filters_all_relative(
                        employees_qs, field, operator, value
                    )
                elif operator in ["is empty", "is not empty"]:
                    filtered = apply_employee_filters_all_date(
                        employees_qs, field, None, None, operator
                    )
                else:
                    continue
            else:
                continue

            and_query &= Q(id__in=filtered.values_list("id", flat=True))

        or_query |= and_query

    return employees_qs.filter(or_query).distinct()


def apply_operator_logic(qs, field_path, value, operator, prop_name=None):
    print("apply_operator_logic", field_path, value, operator)
    value = value or ""

    if operator == "is empty":
        return qs.filter(
            Q(**{f"{field_path}__isnull": True}) | Q(**{f"{field_path}": ""})
        )

    if operator == "is not empty":
        return qs.filter(
            Q(**{f"{field_path}__isnull": False}) & ~Q(**{f"{field_path}": ""})
        )

    if operator == "icontains":
        return qs.filter(**{f"{field_path}__icontains": value})

    if operator == "not_icontains":
        return qs.exclude(**{f"{field_path}__icontains": value}).exclude(
            Q(**{f"{field_path}__isnull": True}) | Q(**{f"{field_path}": ""})
        )

    if operator == "equals":
        return qs.filter(**{f"{field_path}__exact": value})

    if operator == "equals (case-insensitive)":
        return qs.filter(**{f"{field_path}__iexact": value})

    return qs

def apply_employee_filters_all_str(employees_qs, field, value, operator):
    employees_qs = apply_employee_filters_str(employees_qs=employees_qs, field=field, value=value, operator=operator)
    employees_qs = apply_employee_related_filters_str(employees_qs=employees_qs, field=field, value=value, operator=operator)
    return employees_qs


def apply_employee_filters_all_date(employees_qs, field, from_val, to_val, operator=None):
    employees_qs = apply_employee_filters_date(employees_qs, field, from_val, to_val, operator)
    employees_qs = apply_employee_related_filters_date(employees_qs, field, from_val, to_val, operator)
    return employees_qs

def apply_employee_filters_all_relative(employees_qs, field, operator, days):
    if not field or not operator or days is None:
        return employees_qs

    days = int(days)
    today = date.today()
    from_val = None
    to_val = None

    if operator == "more":
        from_val = (today + timedelta(days=days)).isoformat()
    elif operator == "less":
        to_val = (today + timedelta(days=days)).isoformat()
    else:
        return employees_qs

    return apply_employee_filters_all_date(employees_qs, field, from_val, to_val, operator)


def apply_employee_filters_date(employees_qs, field, from_val, to_val, operator=None):
    print("apply_employee_filters_date", field, from_val, to_val, operator)
    if not field:
        return employees_qs

    standard_field_map = {
        "Updated": "updated_at",
        "Created": "created_at",
        "Modified time in exc": "last_modified_time",
        "Created in exc": "datetime_created"
    }
    field_name = standard_field_map.get(field, field)

    if field_name in ["updated_at", "created_at", "last_modified_time", "datetime_created"]:
        if operator == "is empty":
            return employees_qs.filter(**{f"{field_name}__isnull": True})
        elif operator == "is not empty":
            return employees_qs.exclude(**{f"{field_name}__isnull": True})

        filters = {}
        if from_val:
            filters[f"{field_name}__gte"] = datetime.strptime(from_val, "%Y-%m-%d").date()
        if to_val:
            filters[f"{field_name}__lte"] = datetime.strptime(to_val, "%Y-%m-%d").date()
        return employees_qs.filter(**filters)

    # dynamic field from Employees_Parameters
    is_datetime_field = Contacts_Prop.objects.filter(property_name=field, property_type="SystemTime").exists()
    if not is_datetime_field:
        return employees_qs

    if operator == "is empty":
        ids_with_val = Employees_Parameters.objects.filter(
            contacts_prop__property_name=field
        ).exclude(value_date__isnull=True).values("employee")
        return employees_qs.exclude(id__in=list(ids_with_val))

    elif operator == "is not empty":
        ids_with_val = Employees_Parameters.objects.filter(
            contacts_prop__property_name=field,
            value_date__isnull=False
        ).values("employee").distinct()
        return employees_qs.filter(id__in=list(ids_with_val))

    filters = {
        "contacts_prop__property_name": field,
        "value_date__isnull": False
    }
    if from_val:
        filters["value_date__gte"] = make_aware(datetime.strptime(from_val, "%Y-%m-%d"))
    if to_val:
        filters["value_date__lte"] = make_aware(datetime.strptime(to_val, "%Y-%m-%d"))

    matched_ids = Employees_Parameters.objects.filter(**filters).values_list("employee", flat=True).distinct()
    return employees_qs.filter(id__in=matched_ids)


def apply_employee_filters_str(employees_qs, field, value, operator):
    print("apply_employee_filters_str", field, value, operator)
    if not field:
        return employees_qs

    def apply_op(qs, field_path):
        return apply_operator_logic(qs, field_path, value, operator)

    if field == "Last modified name":
        return apply_op(employees_qs, "last_modified_name")

    elif field == "FireCrew":
        return apply_op(employees_qs, "fire_crew__name")

    elif field == "Availability status":
        return apply_op(employees_qs, "availability_entries__availability_status")

    elif field == "Availability location":
        return apply_op(employees_qs, "availability_entries__location")

    elif Contacts_Prop.objects.filter(property_name=field, property_type="String").exists():
        param_path = "employees_parameters_entries__value"

        if operator == "is empty":
            return employees_qs.exclude(
                employees_parameters_entries__contacts_prop__property_name=field,
                employees_parameters_entries__value__isnull=False
            ).exclude(
                employees_parameters_entries__contacts_prop__property_name=field,
                employees_parameters_entries__value__exact=""
            )

        if operator == "is not empty":
            return employees_qs.filter(
                employees_parameters_entries__contacts_prop__property_name=field
            ).exclude(
                employees_parameters_entries__value__isnull=True
            ).exclude(
                employees_parameters_entries__value__exact=""
            )

        lookup = {
            "icontains": "icontains",
            "not_icontains": "icontains",
            "equals": "exact",
            "equals (case-insensitive)": "iexact"
        }.get(operator)

        if not lookup:
            return employees_qs.none()

        filter_expr = {
            f"employees_parameters_entries__contacts_prop__property_name": field,
            f"employees_parameters_entries__value__{lookup}": value
        }

        qs = employees_qs.filter(**filter_expr)
        if operator == "not_icontains":
            qs = employees_qs.exclude(**filter_expr)

        return qs

    return employees_qs


def apply_employee_related_filters_date(employees_qs, field, from_val, to_val, operator=None):
    def dt(val):
        return datetime.strptime(val, "%Y-%m-%d").date()

    annotation_mapping = {
        "Driver's License Exp": Subquery(
            IdentificationDocuments.objects.filter(
                employee=OuterRef("pk"),
                type=IdentificationDocumentsType.DL.name
            ).order_by("-updated_at").values("expiration_date")[:1]
        ),
        "MSPA exp": Subquery(
            MSPA.objects.filter(employee=OuterRef("pk")).order_by("-updated_at").values("expiration_date")[:1]
        ),
        "MSPA issue": Subquery(
            MSPA.objects.filter(employee=OuterRef("pk")).order_by("-updated_at").values("issue_date")[:1]
        ),
        "Dispatch Date": Subquery(
            DispatchingStatus.objects.filter(employee=OuterRef("pk")).order_by("-updated_at").values("date")[:1]
        ),
        "Dispatch ETA": Subquery(
            DispatchingStatus.objects.filter(employee=OuterRef("pk")).order_by("-updated_at").values("ETA")[:1]
        ),
        "Drug Test Date": Subquery(
            DrugTest.objects.filter(employee=OuterRef("pk")).order_by("-updated_at").values("date")[:1]
        ),
        "Nomex In Date": Subquery(
            NomexCheckIn.objects.filter(employee=OuterRef("pk")).order_by("-updated_at").values("date")[:1]
        ),
        "Nomex Out Date": Subquery(
            NomexCheckOut.objects.filter(employee=OuterRef("pk")).order_by("-updated_at").values("date")[:1]
        ),
        "Employee Packet Sent": Subquery(
            EmploymentPacket.objects.filter(employee=OuterRef("pk")).order_by("-updated_at").values("date_sent")[:1]
        ),
        "Employee Packet Signed": Subquery(
            EmploymentPacket.objects.filter(employee=OuterRef("pk")).order_by("-updated_at").values("date_signed")[:1]
        ),
        "IQC Date": Subquery(
            IQCCard.objects.filter(employee=OuterRef("pk")).order_by("-updated_at").values("date")[:1]
        ),
        "Current Assigned Date": Subquery(
            CurrentAssigned.objects.filter(employee=OuterRef("pk")).order_by("-updated_at").values("date")[:1]
        ),
        "Manifest": Subquery(
            CompanyManifest.objects.filter(employee=OuterRef("pk")).order_by("-updated_at").values("date")[:1]
        ),
        "Student Class": Subquery(
            Student.objects.filter(employee=OuterRef("pk")).order_by("-updated_at").values("training_class__date")[:1]
        ),
    }

    if field not in annotation_mapping:
        return employees_qs

    annotation_key = f"annotated__{field.replace(' ', '_').replace("'", '').lower()}"
    employees_qs = employees_qs.annotate(**{
        annotation_key: annotation_mapping[field]
    })

    filters = Q()
    if operator == "is empty":
        filters = Q(**{f"{annotation_key}__isnull": True})
    elif operator == "is not empty":
        filters = Q(**{f"{annotation_key}__isnull": False})
    else:
        if from_val:
            filters &= Q(**{f"{annotation_key}__gte": dt(from_val)})
        if to_val:
            filters &= Q(**{f"{annotation_key}__lte": dt(to_val)})

    return employees_qs.filter(filters)


def apply_employee_related_filters_str(employees_qs, field, value, operator):
    if not field:
        return employees_qs

    field_map = {
        "MSPA number": "mspa_entries__MSPA_number",
        "Dispatch Call Status": "dispatching_status_entries__dispatch_status",
        "Dispatch Category": "dispatching_status_entries__dispatch_category",
        "Nomex In Pants": "nomex_checkin_entries__pants_serial_number",
        "Nomex In Shirt": "nomex_checkin_entries__shirt_serial_number",
        "Nomex Out Pants": "nomex_checkout_entries__pants_serial_number",
        "Nomex Out Shirt": "nomex_checkout_entries__shirt_serial_number",
        "Employee Packet Name": "employment_packet_entries__packet_name",
        "IQC Pack Test": "IQC_card_entries__pack_test",
        "IQC Position": "IQC_card_entries__position",
        "Availability": "availability_entries__availability_status",
        "Rate Of Pay Base": "rate_of_pay_entries__base_rate",
        "Rate Of Pay Bonus": "rate_of_pay_entries__bonus_rate",
        "Rate Of Pay Office": "rate_of_pay_entries__office_rate",
        "Student Test Score": "student_entries__test_score",
        "Student Course": "student_entries__training_class__course__training_type__name",
    }

    if field not in field_map:
        return employees_qs

    lookup_field = field_map[field]
    return apply_operator_logic(employees_qs, lookup_field, value, operator).distinct()
