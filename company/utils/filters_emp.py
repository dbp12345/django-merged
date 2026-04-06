from datetime import date, timedelta
from collections import defaultdict
from django.db.models import (
    Q, F, FloatField, OuterRef, Subquery, ForeignKey, OneToOneField,
    ManyToOneRel, Exists, Count
)
from company.models import Employees, Employees_Parameters
from django.db.models.functions import Cast


# ============================================================================
# UNIVERSAL FILTER SYSTEM
# ============================================================================
# This system automatically handles all filter types without hardcoding
# To disable count annotations: set ENABLE_COUNT_ANNOTATIONS = False below
# ============================================================================

ENABLE_COUNT_ANNOTATIONS = True  # Set to False to disable automatic count annotations


def build_single_filter_q(field_path, operator, value, value_from=None, value_to=None):
    """
    Build Q object for a single filter condition.
    Universal function that works for any field and operator.

    Args:
        field_path: Full field path (e.g., "student_entries__test_score")
        operator: Filter operator (equals, icontains, range, etc.)
        value: Filter value
        value_from: For range operator
        value_to: For range operator

    Returns: Q object or None if invalid
    """
    if not field_path or not operator:
        return None

    # Range operator
    if operator == "range":
        q = Q()
        if value_from:
            q &= Q(**{f"{field_path}__gte": value_from})
        if value_to:
            q &= Q(**{f"{field_path}__lte": value_to})
        return q if q != Q() else None

    # Date operators
    if operator in ["more_then_days", "less_then_days"]:
        delta = int(value or 0)
        cmp_date = date.today() + timedelta(days=delta)
        op = "gte" if operator == "more_then_days" else "lte"
        return Q(**{f"{field_path}__{op}": cmp_date})

    # Numeric operators
    if operator in ["more", "less"]:
        op = "gte" if operator == "more" else "lte"
        return Q(**{f"{field_path}__{op}": value})

    # Empty/not empty
    if operator == "is empty":
        return Q(**{f"{field_path}__isnull": True}) | Q(**{f"{field_path}": ""})

    if operator == "is not empty":
        return Q(**{f"{field_path}__isnull": False}) & ~Q(**{f"{field_path}": ""})

    # Text operators
    lookup_map = {
        "equals": "exact",
        "equals (case-insensitive)": "iexact",
        "icontains": "icontains",
        "not_icontains": "icontains",
        "not_equals": "exact",
        "not_equals (case-insensitive)": "iexact",
    }

    lookup = lookup_map.get(operator)
    if lookup:
        expr = Q(**{f"{field_path}__{lookup}": value})
        # Invert for negative operators
        if operator in ["not_icontains", "not_equals", "not_equals (case-insensitive)"]:
            expr = ~expr
        return expr

    return None


def determine_filter_type(field_path):
    """
    Determine filter type by field path.
    Returns: filter_type string
    """
    if not field_path:
        return "unknown"

    # Count fields (e.g., student_entries_matches_count)
    if field_path.endswith("_matches_count"):
        return "count"

    # Direct model fields
    if field_path.startswith("employees__"):
        return "direct"

    # Parameters (EAV pattern)
    if field_path.startswith("employees_parameters_entries__"):
        return "parameters"

    # One-to-many relations (student_entries, fire_run_entries, etc.)
    if field_path.endswith("_entries") or "__" in field_path:
        # Check if it's a reverse relation (one-to-many)
        parts = field_path.split("__")
        if len(parts) >= 2:
            return "one_to_many"

    # Tags (special case)
    if field_path.startswith("tags"):
        return "tags"

    return "unknown"


def get_relation_name_from_field(field_path):
    """
    Extract relation name from field path.
    Example: "student_entries__test_score" -> "student_entries"
    """
    if "__" in field_path:
        return field_path.split("__")[0]
    return field_path


def apply_direct_filter(qs, filters):
    """Apply filters to direct model fields."""
    condition = Q()
    for f in filters:
        field = f["field"].replace("employees__", "", 1)
        q = build_single_filter_q(
            field, f.get("operator"), f.get("value"),
            f.get("value_from"), f.get("value_to")
        )
        if q:
            condition &= q
    return qs.filter(condition) if condition != Q() else qs


def apply_parameters_filter(qs, filters):
    """Apply filters to Employees_Parameters (EAV pattern)."""
    conditions = Q()

    for group in filters:
        prop_name = None
        value_filters = []

        for f in group:
            field = f["field"]
            if not field.startswith("employees_parameters_entries__"):
                continue

            parts = field.split("__")
            if len(parts) < 2:
                continue

            param_field = parts[-1]
            if param_field == "property_name":
                prop_name = f["value"]
            else:
                value_filters.append(f)

        if not prop_name:
            continue

        sub_q = Employees_Parameters.objects.filter(
            employee_id=OuterRef("pk"),
            contacts_prop__property_name=prop_name
        )

        value_q = Q()
        casts = {}
        is_empty_logic = False  # Track if we have "is empty" operator

        for f in value_filters:
            field_name = f.get("field", "").split("__")[-1]
            operator = f.get("operator")
            value = f.get("value")
            from_val = f.get("value_from")
            to_val = f.get("value_to")

            # Special handling for numeric comparisons
            if operator in ["more", "less"]:
                try:
                    num_val = float(value)
                    ann_name = f"_num_{field_name}"
                    op = "gte" if operator == "more" else "lte"
                    value_q &= Q(**{f"{ann_name}__{op}": num_val})
                    casts[field_name] = ann_name
                    continue
                except (TypeError, ValueError):
                    continue

            # Special handling for "is empty" - build condition for non-empty records
            # This will be used with ~Exists to find employees without non-empty records
            if operator == "is empty":
                is_empty_logic = True
                # Build Q for non-empty records (to exclude them later)
                expr = Q(**{f"{field_name}__isnull": False})
                if field_name not in ["value_date", "value_number"]:
                    expr &= ~Q(**{f"{field_name}": ""})
                value_q |= expr  # Use |= to combine with other conditions
                continue

            if operator == "is not empty":
                expr = Q(**{f"{field_name}__isnull": False})
                if field_name not in ["value_date", "value_number"]:
                    expr &= ~Q(**{f"{field_name}": ""})
                value_q &= expr
                continue

            # Build Q for this filter
            q = build_single_filter_q(field_name, operator, value, from_val, to_val)
            if q:
                value_q &= q

        # Apply casts if needed
        if casts:
            annotate_kwargs = {
                ann: Cast(F(field_name), FloatField())
                for field_name, ann in casts.items()
            }
            sub_q = sub_q.annotate(**annotate_kwargs)

        # Apply filter logic
        if is_empty_logic:
            # For "is empty": exclude employees who have non-empty records matching value_q
            # This finds employees WITHOUT records matching the conditions
            conditions |= ~Exists(sub_q.filter(value_q))
        elif value_q != Q():
            # For regular filters: find employees WITH matching records
            conditions |= Exists(sub_q.filter(value_q))

    return qs.filter(conditions) if conditions != Q() else qs


def apply_one_to_many_filter(qs, filters, relation_name):
    """
    Apply filters to one-to-many relations using Exists.
    Returns: (filtered_qs, filter_q_for_count)
    """
    # Get related model
    try:
        rel_field = Employees._meta.get_field(relation_name)
        if not isinstance(rel_field, ManyToOneRel):
            return qs, None
        related_model = rel_field.related_model
    except Exception:
        return qs, None

    # Find ForeignKey field pointing to Employees
    employee_field_name = "employee"  # Default fallback
    for field in related_model._meta.get_fields():
        if isinstance(field, ForeignKey) and field.related_model == Employees:
            employee_field_name = field.name
            break

    # Build filter Q for related model and count annotation (same filters)
    filter_q = Q()
    count_filter_q = Q()
    negation = False

    for f in filters:
        field = f.get("field", "")
        if not field.startswith(f"{relation_name}__"):
            continue

        target_field = field.replace(f"{relation_name}__", "")
        operator = f.get("operator")
        value = f.get("value")
        from_val = f.get("value_from")
        to_val = f.get("value_to")

        # Handle negation operators
        if operator in ("not_equals", "not_equals (case-insensitive)"):
            negation = True
            lookup = "iexact" if "case-insensitive" in operator else "exact"
            filter_q &= Q(**{f"{target_field}__{lookup}": value})
            count_filter_q &= Q(**{f"{field}__{lookup}": value})
            continue

        # Build Q for related model (without prefix)
        q = build_single_filter_q(target_field, operator, value, from_val, to_val)
        if q:
            filter_q &= q

        # Build Q for count annotation (with prefix)
        count_q = build_single_filter_q(field, operator, value, from_val, to_val)
        if count_q:
            count_filter_q &= count_q

    if filter_q == Q():
        return qs, None

    # Apply filter using Exists
    subquery = related_model.objects.filter(**{employee_field_name: OuterRef("pk")}).filter(filter_q)
    qs = qs.filter(~Exists(subquery) if negation else Exists(subquery))

    return qs, count_filter_q if count_filter_q != Q() else None


def apply_tags_filter(qs, filters):
    """Apply filters to tags (special handling)."""
    for f in filters:
        field = f.get("field", "")
        operator = f.get("operator")
        value = f.get("value") or ""
        target = "tags__name" if "tags__" not in field else field

        # Special handling for equals with comma-separated values
        if operator == "equals":
            vals = [v.strip() for v in value.split(",") if v.strip()]
            if len(vals) > 1:
                qs = qs.filter(tags__name__in=vals).distinct()
            else:
                qs = qs.filter(**{target: value}).distinct()
        # Empty/not empty need count annotation
        elif operator == "is empty":
            qs = qs.annotate(_tag_count=Count("tags")).filter(_tag_count=0)
        elif operator == "is not empty":
            qs = qs.annotate(_tag_count=Count("tags")).filter(_tag_count__gt=0)
        # Other operators use standard Q building
        else:
            q = build_single_filter_q(target, operator, value)
            if q:
                qs = qs.filter(q).distinct() if operator != "not_icontains" else qs.exclude(~q).distinct()

    return qs


def apply_count_filter(qs, filters):
    """Apply filters to count annotations (e.g., student_entries__matches_count__gte=3)."""
    condition = Q()
    for f in filters:
        field = f.get("field", "")
        operator = f.get("operator")
        value = f.get("value")
        try:
            int_value = int(value)
            if operator in ["more", "gte", ">="]:
                condition &= Q(**{f"{field}__gte": int_value})
            elif operator in ["less", "lte", "<="]:
                condition &= Q(**{f"{field}__lte": int_value})
            elif operator == "equals":
                condition &= Q(**{field: int_value})
        except (ValueError, TypeError):
            continue
    return qs.filter(condition) if condition != Q() else qs


def apply_all_filters_with_or(employees_qs, or_filter_groups, group_logic_map=None):
    """
    Universal filter system - applies all filters without hardcoding field types.
    Automatically adds count annotations for one-to-many relations.
    """
    if not or_filter_groups:
        return employees_qs

    # Separate count filters - they need annotations first
    count_filters = []
    regular_filter_groups = []

    for group in or_filter_groups:
        count_group = [f for f in group if determine_filter_type(f.get("field", "")) == "count"]
        regular_group = [f for f in group if determine_filter_type(f.get("field", "")) != "count"]
        if count_group:
            count_filters.extend(count_group)
        if regular_group:
            regular_filter_groups.append(regular_group)

    # Track filtered one-to-many relations for count annotations
    filtered_relations = {}  # {relation_name: Q_object}

    # Process regular filter groups
    or_query = Q()

    for i, group in enumerate(regular_filter_groups):
        qs = employees_qs

        # Group filters by type
        filters_by_type = defaultdict(list)
        for f in group:
            field = f.get("field", "")
            filter_type = determine_filter_type(field)
            filters_by_type[filter_type].append(f)

        # Apply direct filters
        if filters_by_type["direct"]:
            qs = apply_direct_filter(qs, filters_by_type["direct"])

        # Apply parameters filters
        if filters_by_type["parameters"]:
            qs = apply_parameters_filter(qs, [filters_by_type["parameters"]])

        # Apply one-to-many filters
        one_to_many_by_relation = defaultdict(list)
        for f in filters_by_type["one_to_many"]:
            relation_name = get_relation_name_from_field(f.get("field", ""))
            one_to_many_by_relation[relation_name].append(f)

        for relation_name, relation_filters in one_to_many_by_relation.items():
            qs, count_q = apply_one_to_many_filter(qs, relation_filters, relation_name)
            if count_q and ENABLE_COUNT_ANNOTATIONS:
                filtered_relations[relation_name] = count_q

        # Apply tags filters
        if filters_by_type["tags"]:
            qs = apply_tags_filter(qs, filters_by_type["tags"])

        # Apply unknown filters (fallback - try direct application)
        if filters_by_type["unknown"]:
            condition = Q()
            for f in filters_by_type["unknown"]:
                field = f.get("field", "")
                q = build_single_filter_q(
                    field, f.get("operator"), f.get("value"),
                    f.get("value_from"), f.get("value_to")
                )
                if q:
                    condition &= q
            if condition != Q():
                qs = qs.filter(condition)

        # Combine with OR/AND logic
        group_q = Q(id__in=qs.values("id"))
        logic = group_logic_map.get(i, "or")
        if logic == "and":
            or_query &= group_q
        else:
            or_query |= group_q

    employees_qs = employees_qs.filter(or_query).distinct()

    # ============================================================================
    # Add count annotations for filtered one-to-many relations
    # This allows filtering by count (e.g., student_entries__matches_count__gte=3)
    # To disable: set ENABLE_COUNT_ANNOTATIONS = False at top of file
    # ============================================================================
    if ENABLE_COUNT_ANNOTATIONS and filtered_relations:
        count_annotations = {}
        for relation_name, filter_q in filtered_relations.items():
            annotation_name = f"{relation_name}__matches_count"
            count_annotations[annotation_name] = Count(relation_name, filter=filter_q, distinct=True)
        if count_annotations:
            employees_qs = employees_qs.annotate(**count_annotations)
    
    # Apply count filters (they need annotations to exist)
    # Skip count filters for employees_parameters_entries (EAV pattern, not supported)
    if count_filters:
        valid_count_filters = [
            f for f in count_filters
            if not f.get("field", "").startswith("employees_parameters_entries__matches_count")
        ]
        if valid_count_filters:
            employees_qs = apply_count_filter(employees_qs, valid_count_filters)
    # ============================================================================

    return employees_qs


# ============================================================================
# LEGACY FUNCTIONS (kept for backward compatibility if needed)
# ============================================================================

def annotate_with_filtered_latest_subquery(qs, filters, related_prefix, root_model):
    """Legacy function - kept for compatibility."""
    try:
        parts = related_prefix.split("__")
        first = parts[0]

        try:
            rel_field = root_model._meta.get_field(first)
            related_model = rel_field.related_model
            reverse_field = None
            for f in related_model._meta.get_fields():
                if getattr(getattr(f, "related_model", None), "__name__", None) == root_model.__name__:
                    if isinstance(f, (ForeignKey, OneToOneField)):
                        reverse_field = f.name
                        break
                    elif isinstance(f, ManyToOneRel):
                        reverse_field = f.get_accessor_name()
                        break
            if not reverse_field:
                reverse_field = first
        except Exception:
            related_model = None
            reverse_field = None
            for f in root_model._meta.get_fields():
                if isinstance(f, ManyToOneRel):
                    related_model = f.related_model
                    reverse_field = f.get_accessor_name()
                    break
            if related_model is None:
                return qs

        subquery_filter = Q()
        for f in filters:
            field = f.get("field")
            operator = f.get("operator")
            value = f.get("value")
            from_val = f.get("value_from")
            to_val = f.get("value_to")
            target = field.split("__")[-1]

            q = build_single_filter_q(target, operator, value, from_val, to_val)
            if q:
                subquery_filter &= q

        annotations = {}
        for f in filters:
            full_field = f["field"]
            if full_field.startswith(f"{related_prefix}__"):
                target_field = full_field.replace(f"{related_prefix}__", "")
            else:
                target_field = full_field.split("__")[-1]
            ann_name = full_field
            try:
                sub_q = (
                    related_model.objects
                    .filter(**{reverse_field: OuterRef("pk")})
                    .filter(subquery_filter)
                    .order_by("-updated_at")
                )
                annotations[ann_name] = Subquery(sub_q.values(target_field)[:1])
            except Exception:
                continue

        if annotations:
            return qs.annotate(**annotations)
        return qs
    except Exception:
        return qs
