from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django_admin_flexlist import FlexListAdmin
from more_admin_filters import MultiSelectDropdownFilter
from company.models import Employees
from core.admin_panel.admin.TaskAdmin import CategoryTreeFilter
from core.models import Category, HelpTicket
from pdf_plugin.admin_mixin import PDFGenerateMixin


class HelpTicketChildrenInline(admin.TabularInline):
    model = HelpTicket
    fk_name = "parent"
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    # removed: autocomplete_fields (parent is implicit; assigned_to is readonly)
    readonly_fields = ("title", "status", "priority", "assigned_to", "created_at")
    fields = ("title", "status", "priority", "assigned_to", "created_at")
    show_change_link = True
    # Reason: quick visibility of children without opening each one.  # added


class AttachedToFilter(admin.SimpleListFilter):
    title = "Attached to"
    parameter_name = "attached_to"

    def lookups(self, request, model_admin):
        return [
            ("employees", "Employees"),
            ("firecrew", "FireCrew"),
            ("dispatch", "Dispatch"),
            ("equipment_group", "Equipment group"),
            ("saw", "Saw"),
            ("radio", "Radio"),
            ("phone", "Phone"),
            ("truck", "Truck"),
            ("equipment", "Equipment"),
            ("none", "No attachment"),
        ]

    def queryset(self, request, queryset):
        v = self.value()
        if v == "employees":
            return queryset.filter(employees__isnull=False)
        if v == "firecrew":
            return queryset.filter(firecrew__isnull=False)
        if v == "dispatch":
            return queryset.filter(dispatch__isnull=False)
        if v == "equipment_group":
            return queryset.filter(equipment_group__isnull=False)
        if v == "saw":
            return queryset.filter(saw__isnull=False)
        if v == "radio":
            return queryset.filter(radio__isnull=False)
        if v == "phone":
            return queryset.filter(phone__isnull=False)
        if v == "truck":
            return queryset.filter(truck__isnull=False)
        if v == "equipment":
            return queryset.filter(equipment__isnull=False)
        if v == "none":
            return queryset.filter(
                employees__isnull=True,
                firecrew__isnull=True,
                dispatch__isnull=True,
                equipment_group__isnull=True,
                saw__isnull=True,
                radio__isnull=True,
                phone__isnull=True,
                truck__isnull=True,
                equipment__isnull=True,
            )
        return queryset


class AssignedCombinedFilter(admin.SimpleListFilter):
    title = "Assigned"
    parameter_name = "assigned_to_combined"
    MAX_LOOKUPS = 100

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        assigned_ids = list(
            qs.filter(assigned_to__isnull=False)
            .order_by()
            .values_list("assigned_to", flat=True)
            .distinct()[: self.MAX_LOOKUPS]
        )
        assigned_ids = [i for i in assigned_ids if i]
        employees = Employees.objects.filter(pk__in=assigned_ids)
        lookups = [
            ("all", "All"),
            ("me", "Assigned to me"),
            ("unassigned", "Unassigned"),
        ]
        for e in employees:
            label = e
            lookups.append((str(e.pk), label))
        return lookups

    def queryset(self, request, queryset):
        val = self.value()
        if not val or val == "all":
            return queryset
        if val == "me":
            # emp = getattr(request.user, "employee", None)
            # if emp:
            #     return queryset.filter(assigned_to=emp, status__in=["processing", "send"])
            # return queryset.filter(assigned_to__user=request.user, status__in=["processing", "send"])
            # status_filter = Q(status__in=["processing", "send", "unresolved"])

            emp = getattr(request.user, "employee", None)
            my_groups = request.user.groups.values_list("pk", flat=True)

            # мне лично (через Employees и прямого user) ИЛИ на мои группы
            mine = (
                Q(assigned_to=emp)
                | Q(assigned_to__user=request.user)
                | Q(assigned_to_group_id__in=my_groups)
            )
            return queryset.filter(mine).distinct()
            # return queryset.filter(status_filter & mine).distinct()
        if val == "unassigned":
            return queryset.filter(assigned_to__isnull=True)
        try:
            return queryset.filter(assigned_to__pk=int(val))
        except Exception:
            return queryset

    # ---- вот эта штука убирает дефолтный duplicate "All" ----
    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup,
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}
                ),
                "display": title,
            }


class StatusCombinedFilter(admin.SimpleListFilter):
    title = "Status"
    parameter_name = "status_combined"

    def lookups(self, request, model_admin):
        return [
            ("all", "All"),
            ("send", "Not started"),
            ("processing", "Started"),
            ("completed", "Finished"),
            ("unresolved", "Unable to complete"),
            ("waiting", "Waiting for other tasks"),
            ("processing_send", "Not started & Started"),
            ("send_unresolved", "Not started & Unable to complete"),
        ]

    def queryset(self, request, queryset):
        val = self.value()
        if not val or val == "all":
            # By default, exclude "waiting" status tickets (they are hidden)
            return queryset.exclude(status="waiting")
        if val == "processing_send":
            return queryset.filter(status__in=["processing", "send"])
        if val == "send_unresolved":
            return queryset.filter(status__in=["send", "unresolved"])
        return queryset.filter(status=val)

    # переопределяем choices(), чтобы убрать дефолтный дублирующий "All"
    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup,
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}
                ),
                "display": title,
            }


# widget для ясного отображения дерева в выпадашке
class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{"— " * (obj.get_depth() - 1)}{obj.name}'


class AssignedGroupFilter(admin.SimpleListFilter):
    title = "Assigned group"
    parameter_name = "assigned_group"

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        group_ids = list(
            qs.filter(assigned_to_group__isnull=False)
            .order_by()
            .values_list("assigned_to_group", flat=True)
            .distinct()[:100]
        )
        if not group_ids:
            return [
                # ("all", "All"),
                ("none", "No group")
            ]

        names = Group.objects.filter(pk__in=group_ids).values_list("pk", "name")
        return [
            # ("all", "All"),
            ("none", "No group")
        ] + [(str(pk), name) for pk, name in names]

    def queryset(self, request, queryset):
        val = self.value()
        if not val or val == "all":
            return queryset
        if val == "none":
            return queryset.filter(assigned_to_group__isnull=True)
        try:
            return queryset.filter(assigned_to_group_id=int(val))
        except Exception:
            return queryset


class HelpTicketForm(forms.ModelForm):
    children_select = forms.ModelMultipleChoiceField(
        queryset=HelpTicket.objects.none(),
        required=False,
        label="Help tickets",
        help_text="Select existing tickets to link as children.",
    )

    category = CategoryChoiceField(
        queryset=Category.objects.all().order_by("path"), required=False
    )

    class Meta:
        model = HelpTicket
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance

        if instance and instance.pk:
            qs = HelpTicket.objects.exclude(pk=instance.pk)
            if instance.category_id is None:
                qs = qs.filter(category__isnull=True)
            else:
                qs = qs.filter(category_id=instance.category_id)
            self.fields["children_select"].queryset = qs
            self.fields["children_select"].initial = instance.children.all()

            # Filter prerequisite to show only sibling tickets (same parent)
            if "prerequisite" in self.fields:
                qs = HelpTicket.objects.exclude(pk=instance.pk)
                if instance.parent_id:
                    qs = qs.filter(parent_id=instance.parent_id)
                else:
                    qs = qs.filter(parent__isnull=True)
                self.fields["prerequisite"].queryset = qs
        else:
            self.fields.pop("children_select", None)
            # For new instances, show tickets with no parent
            if "prerequisite" in self.fields:
                self.fields["prerequisite"].queryset = HelpTicket.objects.filter(parent__isnull=True)

    def clean(self):
        cleaned = super().clean()
        # enforce same category after user edits category in this form
        if self.instance and self.instance.pk and "children_select" in self.fields:
            current_cat = cleaned.get("category", self.instance.category)
            selected = cleaned.get("children_select")
            if selected is not None:
                # any child not matching current_cat is invalid
                mismatch = selected.exclude(category=current_cat)
                if mismatch.exists():
                    raise forms.ValidationError(
                        "Children must be in the same Category as this ticket."
                    )

        # Validate prerequisite is a sibling (same parent)
        prerequisite = cleaned.get("prerequisite")
        if prerequisite:
            current_parent = cleaned.get("parent") or (self.instance.parent if self.instance else None)
            if prerequisite.parent != current_parent:
                raise forms.ValidationError({
                    "prerequisite": "Prerequisite ticket must be a sibling (have the same parent)."
                })

        return cleaned


@admin.register(HelpTicket)
class HelpTicketAdmin(PDFGenerateMixin, FlexListAdmin):
    form = HelpTicketForm
    list_per_page = 100

    # def changelist_view(self, request, extra_context=None):
    #     if "assigned_to_combined" not in request.GET:
    #         q = request.GET.copy()
    #         q["assigned_to_combined"] = "me"
    #         return HttpResponseRedirect(f"{request.path}?{q.urlencode()}")
    #     return super().changelist_view(request, extra_context)

    inlines = (HelpTicketChildrenInline,)

    def changelist_view(self, request, extra_context=None):
        q = request.GET.copy()
        changed = False
        if not q.get("assigned_to_combined"):
            q["assigned_to_combined"] = "me"
            changed = True
        if not q.get("status_combined"):
            q["status_combined"] = "send_unresolved"
            changed = True
        if changed:
            return HttpResponseRedirect(f"{request.path}?{q.urlencode()}")
        return super().changelist_view(request, extra_context)

    autocomplete_fields = (
        "employees",
        "firecrew",
        "dispatch",
        "equipment_group",
        "saw",
        "radio",
        "phone",
        "truck",
        "equipment",
        "created_by",
        "created_for",
        "assigned_to",
        "parent",
        "prerequisite",
        # NOTE: Group autocomplete works only if GroupAdmin has search_fields.
        # If not, use raw_id_fields fallback below.  # added
        # "assigned_to_group",  # optional if GroupAdmin supports it  # added
    )

    # fallback for huge tables (если автокомплит не работает) — добавь raw_id_fields
    # raw_id_fields = (
    #     "employees",
    #     "firecrew",
    #     "dispatch",
    #     "equipment_group",
    #     "saw",
    #     "radio",
    #     "phone",
    #     "truck",
    #     "equipment",
    #     "created_by",
    #     "created_for",
    #     "assigned_to",
    #     "assigned_to_group",
    # )

    list_display = (
        "updated_at",
        "title",
        # "parent",
        "parent_link",
        "created_for",
        "assigned_to",
        "assigned_to_group",
        "get_attached_display",
        "status",
        "priority",
        "document_preview",
        "category",
        "tools",
        "created_by",
        "created_by_admin",
        "children_count_col",
    )

    _base_fields = (
        "title",
        "parent",
        "prerequisite",
        # "parent_link",
        "employees",
        "firecrew",
        "dispatch",
        "equipment_group",
        "saw",
        "radio",
        "phone",
        "truck",
        "equipment",
        "status",
        "priority",
        "created_for",
        (
            "assigned_to",
            "assigned_to_group",
        ),
        "body",
        "note",
        ("document", "document_preview"),
        "category",
        "tools",
        "created_by",
        "created_by_admin",
        "date_completed",
        ("created_at", "updated_at"),
    )

    ordering = (
        "-priority",
        "-updated_at",
    )

    fields = (
        "title",
        # "parent",
        "parent_link",
        "prerequisite",
        "employees",
        "firecrew",
        "dispatch",
        "equipment_group",
        "saw",
        "radio",
        "phone",
        "truck",
        "equipment",
        "status",
        "priority",
        "created_for",
        (
            "assigned_to",
            "assigned_to_group",
        ),
        "body",
        "note",
        ("document", "document_preview"),
        "category",
        "tools",
        "created_by",
        "created_by_admin",
        # "date_opened",
        "date_completed",
        ("created_at", "updated_at"),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "parent",
            "prerequisite",
            "assigned_to",
            "created_for",
            "assigned_to_group",
            "category",
        )

    def get_fields(self, request, obj=None):
        # add children_select only on change form
        if obj:
            return ("parent_link",) + self._base_fields + ("children_select",)
        return self._base_fields

    def get_readonly_fields(self, request, obj=None):
        ro = ("created_by", "created_by_admin", "created_at", "updated_at", "document_preview")
        if obj:
            return ro + ("parent_link",)
        return ro

        # если created_by_admin установлен и НЕ равен текущему юзеру — делаем почти всё readonly
        # creator = getattr(obj, "created_by_admin", None)
        # if creator and creator != request.user:
        if False:
            return (
                "title",
                "employees",
                "firecrew",
                "dispatch",
                "equipment_group",
                "saw",
                "radio",
                "phone",
                "truck",
                "equipment",
                "priority",
                "created_for",
                "assigned_to",
                "body",
                "document",
                "category",
                "created_by",
                "created_by_admin",
                "date_completed",
                "created_at",
                "updated_at",
            )
        else:
            return (
                "created_by",
                "created_by_admin",
                "created_at",
                "updated_at",
            )

    readonly_fields = (
        # "date_opened",
        "created_by",
        "created_by_admin",
        "created_at",
        "updated_at",
        "document_preview",
    )

    list_filter = (
        AssignedCombinedFilter,
        AssignedGroupFilter,
        AttachedToFilter,
        StatusCombinedFilter,
        "priority",
        CategoryTreeFilter,
        "tools",
        ("tools", MultiSelectDropdownFilter),
        # ("assigned_to", admin.RelatedOnlyFieldListFilter),
        ("created_for", admin.RelatedOnlyFieldListFilter),
        ("created_by", admin.RelatedOnlyFieldListFilter),
        ("created_by_admin", admin.RelatedOnlyFieldListFilter),
        # ("created_for", DALFRelatedFieldAjax),
        # ("assigned_to", DALFRelatedFieldAjax),
    )
    search_fields = (
        "title",
        "truck__license_plate",
    )

    def get_attached_display(self, obj):
        name, instance = obj.get_attached()
        if not name:
            return "—"
        return name

    get_attached_display.short_description = "Attached"

    def parent_link(self, obj):
        if not obj.parent_id:
            return "—"
        url = reverse("admin:core_helpticket_change", args=[obj.parent_id])
        return format_html('<a href="{}">{}</a>', url, obj.parent)

    parent_link.short_description = "Parent"
    parent_link.admin_order_field = "parent"

    def children_count_col(self, obj):
        return obj.children.count()

    children_count_col.short_description = "Children"

    def save_model(self, request, obj, form, change):
        if not change and request.user.is_authenticated:
            obj.created_by_admin = request.user
            employee = getattr(request.user, "employee", None)
            if employee and not obj.created_by:
                obj.created_by = employee
        super().save_model(request, obj, form, change)

        # NEW: apply children_select to re-parent existing tickets
        selected = form.cleaned_data.get("children_select")
        if selected is not None:
            prev = set(obj.children.all())
            new = set(selected)

            # attach newly selected (respect clean() to avoid cycles)
            for child in (new - prev):
                child.parent = obj
                child.save()  # triggers full_clean

            # detach unselected former children
            for child in (prev - new):
                child.parent = None
                child.save()  # triggers full_clean

    class Media:
        js = (
            "admin/js/help_ticket_attach.js",
            "admin/js/tools_labels.js",
        )
        css = {"all": (
            "admin/css/help_ticket_attach.css",
        )}
