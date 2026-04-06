from dal import autocomplete
from django.contrib import admin
from django import forms
from django.contrib.admin import RelatedOnlyFieldListFilter, SimpleListFilter
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django_admin_flexlist import FlexListAdmin

from django.db.models import (
    Case, When, Value, IntegerField, CharField, OuterRef, Subquery, F, Count
)
from django.db.models.functions import Coalesce
from django.db.models.expressions import Func

from company.models import Employees_Parameters, Crew
from dispatch.models import Invoice
from dispatch.models.Dispatch import (
    Dispatch,
    Status,
    Equipment_group,
    Truck,
    Saw,
    Phone,
    Radio,
    Nomex,
)
from dispatch.models.Equipment import Equipment
from pdf_plugin.admin_mixin import PDFGenerateMixin


class DispatchForm(forms.ModelForm):
    crews = forms.ModelMultipleChoiceField(
        queryset=Crew.objects.none(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="crew-autocomplete",
            forward=["instance_id"],
        ),
    )

    class Meta:
        model = Dispatch
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance

        if instance.pk and "instance_id" not in self.data:
            self.data = self.data.copy()
            self.data["instance_id"] = str(instance.pk)

        if instance.pk:
            selected_qs = Crew.objects.filter(dispatch=instance)  # если FK другое имя — замени
            self.fields["crews"].queryset = Crew.objects.filter(dispatch__isnull=True) | selected_qs
            self.fields["crews"].initial = selected_qs
        else:
            self.fields["crews"].queryset = Crew.objects.filter(dispatch__isnull=True)

    def clean_equipment_group(self):
        groups = self.cleaned_data.get("equipment_group")

        # Only validate when the field actually changed
        if "equipment_group" not in self.changed_data:
            return groups

        # New object: treat all as added
        if not self.instance.pk:
            added_qs = groups
        else:
            # Compute only newly added items
            old_ids = set(self.instance.equipment_group.values_list("id", flat=True))
            new_ids = set(groups.values_list("id", flat=True))
            added_ids = new_ids - old_ids
            if not added_ids:
                return groups
            added_qs = groups.model.objects.filter(id__in=added_ids)

        bad = added_qs.filter(status=Status.ON_FIRE)
        if bad.exists():
            names = ", ".join(bad.values_list("name", flat=True))
            raise forms.ValidationError(f"Already 'On fire' and cannot be assigned: {names}")
        return groups

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()

        # sync crews: set dispatch for selected, clear for others
        selected = list(self.cleaned_data.get("crews", []))
        selected_ids = [c.pk for c in selected]

        # detach crews previously linked but not selected now
        Crew.objects.filter(dispatch=instance).exclude(pk__in=selected_ids).update(dispatch=None)

        # attach selected crews
        for c in selected:
            if c.dispatch_id != instance.pk:
                c.dispatch = instance
                c.save()

        return instance


class StatusCustomFilter(SimpleListFilter):
    title = "Status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return [
            ("all", "All"),
            *[(choice.value, choice.label) for choice in Status],
            ("multiple", 'On Fire + Scheduled'),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == "multiple":
            return queryset.filter(status__in=[Status.ON_FIRE, Status.SCHEDULED])
        elif value in Status.values:
            return queryset.filter(status=value)
        return queryset  # "all" или None

    def choices(self, changelist):
        # Убираем дефолтный `All` (value="?")
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == lookup,
                "query_string": changelist.get_query_string({self.parameter_name: lookup}),
                "display": title,
            }


class CustomDispatchChangeList(ChangeList):
    def get_ordering(self, request, queryset):
        ordering = super().get_ordering(request, queryset)
        return ("status_priority", *ordering)


class CrewInline(admin.TabularInline):
    model = Crew

    def has_add_permission(self, request, obj=None):
        return False

    autocomplete_fields = ("fire",)
    fields = (
        # "updated_at_link",
        "crew_name",
        # "crew_boss",
        "fire",
        "c_number",
        "contract",
    )
    readonly_fields = (
        "updated_at_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-id",)

    @admin.display(description="Updated At")
    def updated_at_link(self, instance):
        url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.id])
        return format_html(
            '<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>',
            url,
            instance.updated_at.strftime("%m/%d/%Y %H:%M"),
        )


@admin.register(Dispatch)
class DispatchAdmin(PDFGenerateMixin, FlexListAdmin):
    @admin.display(description="Crew")
    def crew_link(self, obj):
        crew_obj = obj.crew or obj.crew_archived
        crew_id = crew_obj.id if crew_obj else ""

        url = reverse("crews_management") + "?" + urlencode({"crew_id": crew_id})
        return format_html(
            '<a class="" href="{}">{}</a>',
            url,
            crew_obj,
        )

    @admin.display(description="Contract")
    def contract_link(self, obj):
        contract = obj.contract
        if contract:
            url = reverse("admin:dispatch_contracts_change", args=[contract.id])
            return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, contract.__str__())
        return "-"

    @admin.display(description="Fire")
    def fire_link(self, obj):
        fire = obj.fire
        if fire:
            url = reverse("admin:company_fire_change", args=[fire.id])
            return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, fire.__str__())
        return "-"

    def get_changelist(self, request, **kwargs):
        return CustomDispatchChangeList

    # CHANGED: добавляем аннотацию, собирающую строку в точности как __str__
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # boss surname from Employees_Parameters(property_name='surname')
        boss_surname_sq = Subquery(
            Employees_Parameters.objects
            .filter(employee_id=OuterRef("crew__crew_boss_id"),
                    contacts_prop__property_name="surname")
            .values("value")[:1]
        )

        # if surname == '' → treat as NULL to fall back to crew__name
        boss_or_crew = Coalesce(
            NullIf(boss_surname_sq, Value("")),
            F("crew__name"),
            output_field=CharField(),
        )

        qs = qs.annotate(
            status_priority=Case(
                When(status=Status.ON_FIRE, then=Value(0)),
                When(status=Status.SCHEDULED, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
            # EXACT order as in __str__:
            # [boss surname or crew], ec_number, fire_number, incident_name, state
            str_for_search=ConcatWS(
                Value(", "),
                boss_or_crew,
                F("ec_number"),
                F("fire__fire_number"),
                F("fire__incident_name"),
                F("fire__state"),
                output_field=CharField(),
            ),
        )

        return qs.prefetch_related(
            "equipment_group",
            "equipment_group__truck_entries",
            "equipment_group__saws_entries",
            "equipment_group__phone_entries",
            "equipment_group__radio_entries",
            "equipment_group__nomex_entries",
            "equipment_group__equipment_entries",
        )

    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    form = DispatchForm

    list_per_page = 100
    search_fields = (
        "str_for_search",
        "crew__name",
        # "ec_number",
        "crew_archived__name",
        # "fire__incident_name",
        # "fire__state",
        "fire__agency",
        # "fire__fire_number",
        "company_rel__name",
    )
    autocomplete_fields = ("crew", "crew_archived", "contract", "fire", "equipment_group")
    list_display_links = ("updated_at",)

    inlines = (
        CrewInline,
    )

    # list_display_links = ("updated_at",)

    def get_fieldsets(self, request, obj=None):
        return ((None, {"fields": self.fields}),)

    @admin.display(description="")
    def all_links(self, instance):
        if instance.pk:
            return format_html(
                '<a href="{}" target="_blank" rel="noreferrer noopener">ODF Hand Crew Manifest.docx</a><br/>'
                '<a href="{}" target="_blank" rel="noreferrer noopener">ODF Eqp Manifest.pdf</a><br/>'
                '<a href="{}" target="_blank" rel="noreferrer noopener">ODF Extension Form.docx</a><br/>'
                '<a href="{}" target="_blank" rel="noreferrer noopener">VIPR Crew Manifest.docx</a><br/>'
                '<a href="{}" target="_blank" rel="noreferrer noopener">VIPR Eqp Manifest.pdf</a><br/>'
                '<a href="{}" target="_blank" rel="noreferrer noopener">VIPR Extension Form.pdf</a><br/>',
                reverse("dispatch_docs_odf_crew_manifest_docx_get") + "?" + urlencode({"id": str(instance.pk)}),
                reverse("dispatch_docs_odf_eqp_manifest_pdf_get") + "?" + urlencode({"id": str(instance.pk)}),
                reverse("dispatch_docs_odf_extension_form_docx_get") + "?" + urlencode({"id": str(instance.pk)}),
                reverse("dispatch_docs_vipr_crew_manifest_docx_get") + "?" + urlencode({"id": str(instance.pk)}),
                reverse("dispatch_vipr_eqp_manifest_pdf_get") + "?" + urlencode({"id": str(instance.pk)}),
                reverse("dispatch_vipr_extension_form_pdf_get") + "?" + urlencode({"id": str(instance.pk)}),
            )
        return "-"

    @admin.display(description="Global status")
    def set_global_status(self, obj):
        return format_html(
            '<a class="button set_global_status on_fire" href="{}">Set "On Fire"</a>'
            '<a class="button set_global_status not_on_fire" href="{}">Set "Not On Fire"</a>',
            reverse(
                "dispatch_set_global_status",
                kwargs={"obj_id": obj.id, "status": Status.ON_FIRE},
            ),
            reverse(
                "dispatch_set_global_status",
                kwargs={"obj_id": obj.id, "status": Status.NOT_ON_FIRE},
            ),
        )

    @admin.display(description="DOF")
    def day_on_fire_link(self, instance):
        if instance.pk:
            url = reverse("day_on_fire_service") + "?" + urlencode({"dispatch_id": str(instance.pk)})
            return format_html('<a href="{}" target="_blank" rel="noopener noreferrer">DOF</a>', url)
        return "-"

    @admin.display(description="Company")
    def company_rel_link(self, instance):
        company = instance.company_rel
        if company:
            url = reverse("admin:company_company_change", args=[company.id])
            return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, company.__str__())
        return "-"

    @admin.display(description="Invoices")
    def invoices_column(self, obj):
        invs = obj.invoices_entries.all()
        if not invs.exists():
            return "-"

        app = Invoice._meta.app_label
        model = Invoice._meta.model_name

        def fmt_amount(x):
            return f"${x:,.2f}" if x is not None else ""

        def make_row(inv):
            inv_url = reverse(f"admin:{app}_{model}_change", args=[inv.pk])

            meta_parts = []
            if inv.invoice_amount is not None:
                meta_parts.append(fmt_amount(inv.invoice_amount))
            if inv.status:
                meta_parts.append(inv.status)
            meta_html = " · ".join(meta_parts)

            return format_html(
                '<li style="margin:0; padding:6px 0; border-bottom:1px solid #eee;">'
                '<div><a href="{}"><strong>{}</strong></a></div>'
                '<div style="font-size:12px; color:#555;">{}</div>'
                '</li>',
                inv_url,
                inv.invoice_number or format_html("Invoice #{}", inv.pk),
                meta_html,
            )

        rows = [make_row(inv) for inv in invs]
        return format_html(
            '<ul style="list-style:none; margin:0; padding:0; line-height:1.35;">{}</ul>',
            format_html_join("", "{}", ((r,) for r in rows)),
        )

    @admin.display(description="Contract info")
    def contract_info(self, instance):
        if not instance or not instance.pk:
            return "-"

        contract = getattr(instance, "contract", None)
        if not contract:
            return "-"

        number = getattr(contract, "number", None) or "-"

        # Safe file URLs: only if file is set and has .url
        award_file = getattr(contract, "award_sheet_file", None)
        award_url = getattr(award_file, "url", None) if award_file else None

        full_file = getattr(contract, "full_contract", None)
        full_url = getattr(full_file, "url", None) if full_file else None

        parts = [format_html("<li>Number: {}</li>", number)]
        parts.append(
            format_html(
                '<li>{}</li>',
                format_html('<a href="{}" target="_blank" rel="noreferrer noopener">Award sheet file</a>', award_url)
                if award_url else ""
            )
        )
        parts.append(
            format_html(
                '<li>{}</li>',
                format_html('<a href="{}" target="_blank" rel="noreferrer noopener">Full Contract</a>', full_url)
                if full_url else ""
            )
        )
        return format_html("<ul>{}</ul>", format_html("".join(parts)))

    @admin.display(description="Equipment groups")
    def equipment_groups_str(self, obj):
        names = obj.equipment_group.values_list("name", flat=True)
        return ", ".join(names) if names else "-"

    list_display = (
        "updated_at",
        "__str__",
        # "company",
        "company_rel_link",
        "crew_link",
        "contract_link",
        "invoices_column",
        "ec_number",
        "first_operational_period",
        "fourteenth_operational_period",
        "manifest_preview",
        "resource_order_preview",
        "status",
        "camp_location",
        "working_location",
        "needs_maintenance",
        "notes",
        "fire_link",
        # "equipment_groups_str",
        "all_equipment_display",
        "all_links",
        "set_global_status",
        "day_on_fire_link",
        # "modified_by",
    )

    list_editable = (
        # "first_operational_period",
        # "fourteenth_operational_period",
        "status",
        # "camp_location",
        # "working_location",
        # "needs_maintenance",
        # "company",
    )
    ordering = ("-updated_at",)

    fields = (
        "equipment_group",
        ("crew", "crew_archived"),
        "fire",
        "contract",
        "contract_info",
        "invoices_column",
        "ec_number",
        "manifest",
        "resource_order",
        # ("manifest", "manifest_preview"),
        # ("resource_order", "resource_order_preview"),
        # "equipment_groups_str",
        "all_equipment_display",
        "first_operational_period",
        "fourteenth_operational_period",
        "status",
        "camp_location",
        "working_location",
        "needs_maintenance",
        # "company",
        "company_rel",
        "notes",
        "set_global_status",
        "day_on_fire_link",
        ("updated_at", "modified_by"),
        "all_links",
        "crews",
    )
    readonly_fields = (
        "manifest_preview",
        "resource_order_preview",
        "all_equipment_display",
        "contract_info",
        "invoices_column",
        "updated_at",
        "modified_by",
        "all_links",
        "set_global_status",
        "day_on_fire_link",
        "equipment_groups_str",
    )

    list_filter = (
        ("crew", RelatedOnlyFieldListFilter),
        ("crew_archived", RelatedOnlyFieldListFilter),
        ("fire", RelatedOnlyFieldListFilter),
        ("contract", RelatedOnlyFieldListFilter),
        ("equipment_group", RelatedOnlyFieldListFilter),
        StatusCustomFilter,
        # "company",
        "company_rel",
        "needs_maintenance",
    )

    def changelist_view(self, request, extra_context=None):
        if "status" not in request.GET:
            q = request.GET.copy()
            q["status"] = "multiple"
            return HttpResponseRedirect(f"{request.path}?{q.urlencode()}")
        return super().changelist_view(request, extra_context)

    @admin.display(description="Equipment")
    def all_equipment_display(self, obj):
        groups = list(obj.equipment_group.all())
        if not groups:
            return "-"

        def render_items(title, items):
            if not items:
                return ""

            def link_for(item):
                app = item._meta.app_label
                model = item._meta.model_name
                url = reverse(f"admin:{app}_{model}_change", args=[item.pk])
                return format_html('<a href="{}" target="_blank" style="color:#000">{}</a>', url, str(item))

            return format_html(
                "<strong>{}</strong><ul style='font-style: italic; margin: 0 0 5px 10px;'>{}</ul>",
                title,
                format_html_join("", "<li style='font-weight: normal;'>{}</li>", ((link_for(i),) for i in items)),
            )

        chunks = []
        for eg in groups:
            section_parts = [
                render_items("Truck:", eg.truck_entries.all()),
                render_items("Saw:", eg.saws_entries.all()),
                render_items("Phone:", eg.phone_entries.all()),
                render_items("Radio:", eg.radio_entries.all()),
                render_items("Nomex:", eg.nomex_entries.all()),
                render_items("Equipment:", eg.equipment_entries.all()),
            ]
            if any(section_parts):
                chunks.append(
                    format_html(
                        '<div style="margin-bottom:8px;">'
                        '<div><strong>Group: <a href="{}" target="_blank" style="color:#000">{}</a></strong></div>{}'
                        '</div>',
                        reverse(
                            f"admin:{eg._meta.app_label}_{eg._meta.model_name}_change",
                            args=[eg.pk],
                        ),
                        eg.name,
                        mark_safe("".join(section_parts)),
                    )
                )

        return mark_safe("".join(chunks)) if chunks else "-"

    class Media:
        js = (
            "admin/dispatch/dispatch_row_highlight.js",
        )
        css = {
            "all": (
                "admin/dispatch/dispatch_row_highlight.css",
                "admin/dispatch/global_status.css",
            )
        }

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        for name in ("crew", "crew_archived", "fire", "contract"):
            f = form.base_fields.get(name)
            if f and isinstance(f.widget, RelatedFieldWidgetWrapper):
                f.widget.can_delete_related = False  # как и было

        if obj and obj.status == Status.NOT_ON_FIRE:
            for name in (
                    "crew",
                    "crew_archived",
                    "equipment_group",
                    "fire",
                    "contract",
                    "ec_number",
                    "first_operational_period",
                    "fourteenth_operational_period",
                    "camp_location",
                    "working_location",
                    "needs_maintenance",
                    # "company",
                    "company_rel",
                    "notes",
            ):
                if name in form.base_fields:
                    form.base_fields[name].disabled = True

                for name_a in ("crew", "crew_archived", "fire", "contract", "equipment_group"):
                    f = form.base_fields.get(name_a)
                    if f and isinstance(f.widget, RelatedFieldWidgetWrapper):
                        f.widget.can_add_related = False

        return form


class EquipmentGroupForm(forms.ModelForm):
    truck = forms.ModelMultipleChoiceField(
        queryset=Truck.objects.none(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="truck-autocomplete",
            forward=["instance_id"]
        )
    )
    saw = forms.ModelMultipleChoiceField(
        queryset=Saw.objects.none(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="saw-autocomplete",
            forward=["instance_id"],
        )
    )
    phone = forms.ModelMultipleChoiceField(
        queryset=Phone.objects.none(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="phone-autocomplete",
            forward=["instance_id"]
        )
    )
    radio = forms.ModelMultipleChoiceField(
        queryset=Radio.objects.none(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="radio-autocomplete",
            forward=["instance_id"]
        )
    )
    nomex = forms.ModelMultipleChoiceField(
        queryset=Nomex.objects.none(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="nomex-autocomplete",
            forward=["instance_id"]
        )
    )
    equipment = forms.ModelMultipleChoiceField(
        queryset=Equipment.objects.none(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="equipment-autocomplete",
            forward=["instance_id"]
        )
    )

    class Meta:
        model = Equipment_group
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance

        if instance.pk and "instance_id" not in self.data:
            self.data = self.data.copy()
            self.data["instance_id"] = str(instance.pk)

        if instance.pk:
            for field_name, related_name, model in [
                ("truck", "truck_entries", Truck),
                ("saw", "saws_entries", Saw),
                ("phone", "phone_entries", Phone),
                ("radio", "radio_entries", Radio),
                ("nomex", "nomex_entries", Nomex),
                ("equipment", "equipment_entries", Equipment),
            ]:
                selected = getattr(instance, related_name).all()
                if model == Equipment:
                    # Equipment uses ManyToMany, so filter differently
                    # Get Equipment that doesn't have this instance OR already selected
                    unassigned = Equipment.objects.exclude(equipment_group=instance)
                    self.fields[field_name].queryset = (unassigned | selected).distinct()
                else:
                    self.fields[field_name].queryset = model.objects.filter(equipment_group__isnull=True) | selected
                self.fields[field_name].initial = selected
        else:
            self.fields["truck"].queryset = Truck.objects.filter(equipment_group__isnull=True)
            self.fields["saw"].queryset = Saw.objects.filter(equipment_group__isnull=True)
            self.fields["phone"].queryset = Phone.objects.filter(equipment_group__isnull=True)
            self.fields["radio"].queryset = Radio.objects.filter(equipment_group__isnull=True)
            self.fields["nomex"].queryset = Nomex.objects.filter(equipment_group__isnull=True)
            # Equipment uses ManyToMany, so filter for items with no equipment_group
            self.fields["equipment"].queryset = Equipment.objects.annotate(
                eg_count=Count('equipment_group')
            ).filter(eg_count=0)

        # Расширяем queryset выбранными из POST
        # for field_name, model in [
        #     ("phone", Phone),
        #     ("nomex", Nomex),
        #     ("radio", Radio),
        #     ("saw", Saw),
        #     ("truck", Truck),
        # ]:
        #     try:
        #         ids = [int(x) for x in self.data.getlist(field_name)]
        #         if ids:
        #             self.fields[field_name].queryset |= model.objects.filter(pk__in=ids)
        #     except Exception as e:
        #         print(f"Patch queryset failed for {field_name}: {e}")

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()

        if instance.pk:
            for field_name, model, related_name in [
                ("truck", Truck, "truck_entries"),
                ("saw", Saw, "saws_entries"),
                ("phone", Phone, "phone_entries"),
                ("radio", Radio, "radio_entries"),
                ("nomex", Nomex, "nomex_entries"),
                ("equipment", Equipment, "equipment_entries"),
            ]:
                if model == Equipment:
                    # Equipment uses ManyToMany, so use set() instead
                    getattr(instance, related_name).set(self.cleaned_data.get(field_name, []))
                else:
                    getattr(instance, related_name).exclude(
                        pk__in=[obj.pk for obj in self.cleaned_data.get(field_name, [])]
                    ).update(equipment_group=None)
                    for obj in self.cleaned_data.get(field_name, []):
                        if obj.equipment_group_id != instance.pk:
                            obj.equipment_group = instance
                            obj.save()

        # if instance.pk:
        #     instance.phone_entries.update(equipment_group=None)
        #     for obj in self.cleaned_data.get("phone", []):
        #         obj.equipment_group = instance
        #         obj.save()
        #
        #     instance.nomex_entries.update(equipment_group=None)
        #     for obj in self.cleaned_data.get("nomex", []):
        #         obj.equipment_group = instance
        #         obj.save()
        #
        #     instance.radio_entries.update(equipment_group=None)
        #     for obj in self.cleaned_data.get("radio", []):
        #         obj.equipment_group = instance
        #         obj.save()
        #
        #     instance.saws_entries.update(equipment_group=None)
        #     for obj in self.cleaned_data.get("saw", []):
        #         obj.equipment_group = instance
        #         obj.save()
        #
        #     instance.truck_entries.update(equipment_group=None)
        #     for obj in self.cleaned_data.get("truck", []):
        #         obj.equipment_group = instance
        #         obj.save()

        return instance

    # def save_m2m(self):
    #     pass


@admin.register(Equipment_group)
class EquipmentGroupAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    form = EquipmentGroupForm

    list_per_page = 100
    search_fields = ("name",)
    # autocomplete_fields = ("dispatch")
    # list_display_links = ("updated_at",)
    list_display_links = ("updated_at",)

    list_display = (
        "updated_at",
        "name",
        "all_equipment_display",
        "status",
        "needs_maintenance",
        "notes",
        # "dispatch",
        # "modified_by",
    )
    list_editable = (
        "status",
        "needs_maintenance",
        # "notes",
        # "crew",
    )
    ordering = ("-updated_at",)

    fields = (
        "name",
        # "dispatch",
        "truck",
        "saw",
        "phone",
        "radio",
        "nomex",
        "equipment",
        "status",
        "needs_maintenance",
        "notes",
        ("updated_at", "modified_by")
    )
    readonly_fields = (
        "updated_at",
        "modified_by",
    )

    list_filter = (
        "status",
        "needs_maintenance",
    )

    @admin.display(description="Equipment")
    def all_equipment_display(self, obj):
        def render_items(title, items):
            if not items:
                return ""

            def link_for(item):
                app = item._meta.app_label
                model = item._meta.model_name
                url = reverse(f"admin:{app}_{model}_change", args=[item.pk])
                return format_html('<a href="{}" target="_blank">{}</a>', url, str(item))

            return format_html(
                "<strong>{}</strong><ul style='font-style: italic; margin: 0 0 5px 10px;'>{}</ul>",
                title,
                format_html_join("", "<li style='font-weight: normal;'>{}</li>", ((link_for(i),) for i in items)),
            )

        if not obj:
            return "-"

        eg = obj

        section_parts = [
            render_items("Truck:", eg.truck_entries.all()),
            render_items("Saw:", eg.saws_entries.all()),
            render_items("Phone:", eg.phone_entries.all()),
            render_items("Radio:", eg.radio_entries.all()),
            render_items("Nomex:", eg.nomex_entries.all()),
            render_items("Equipment:", eg.equipment_entries.all()),
        ]
        return mark_safe("".join(section_parts)) if any(section_parts) else "-"
    # inlines = (
    #     NomexInline,
    #     RadioInline,
    #     SawInline,
    #     TruckInline,
    # )


class ConcatWS(Func):
    function = "CONCAT_WS"


class NullIf(Func):
    function = "NULLIF"
