# from django import forms
from dalf.admin import DALFModelAdmin, DALFRelatedFieldAjax
from django.contrib import admin
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django_admin_flexlist import FlexListAdmin

from dispatch.models import Contracts, Dispatch
from pdf_plugin.admin_mixin import PDFGenerateMixin


class DispatchInline(admin.TabularInline):
    model = Dispatch

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Equipment groups")
    def equipment_groups_str(self, obj):
        names = obj.equipment_group.values_list("name", flat=True)
        return ", ".join(names) if names else "-"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            "equipment_group",
        )

    show_change_link = True
    can_delete = False
    extra = 0

    fields = (
        "crew",
        "fire",
        "contract",
        "equipment_groups_str",
        "manifest",
        "resource_order",
        "modified_by",
        "updated_at",
    )
    readonly_fields = (
        "crew",
        "fire",
        "contract",
        "equipment_groups_str",
        "manifest",
        "resource_order",
        "modified_by",
        "updated_at",
    )

    ordering = ("-updated_at",)


#     # autocomplete_fields = ["..."]  # что тебе надо, можно оставить пустым

# class ContractsForm(forms.ModelForm):
#     dispatches = forms.ModelMultipleChoiceField(
#         queryset=Dispatch.objects.filter(contract__isnull=True),
#         required=False,
#         widget=admin.widgets.FilteredSelectMultiple("Dispatches", is_stacked=False)
#     )
#
#     class Meta:
#         model = Contracts
#         fields = "__all__"
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         if self.instance.pk:
#             self.fields["dispatches"].queryset = (
#                 Dispatch.objects.filter(contract__isnull=True) |
#                 Dispatch.objects.filter(contract=self.instance)
#             )
#             self.fields["dispatches"].initial = self.instance.dispatch_entries.all()
#
#     def save(self, commit=True):
#         instance = super().save(commit=False)
#         if commit:
#             instance.save()
#
#         if instance.pk:
#             # Unbind previous
#             Dispatch.objects.filter(contract=instance).update(contract=None)
#
#             # Rebind selected
#             for d in self.cleaned_data["dispatches"]:
#                 d.contract = instance
#                 d.save()
#
#         return instance


@admin.register(Contracts)
class ContractsAdmin(PDFGenerateMixin, FlexListAdmin, DALFModelAdmin):
    # form = ContractsForm

    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    @admin.display(description="Company")
    def company_rel_link(self, instance):
        company = instance.company_rel
        if company:
            url = reverse("admin:company_company_change", args=[company.id])
            return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, company.__str__())
        return "-"

    list_per_page = 100
    search_fields = (
        "number",
        "award_number",
        "resource_number",
        "type_category",
        "type_number",
        "dispatch_address",
        "region",
        "agency",
        "rate",
        "truck__license_plate",
        "truck__vin_number",
        "truck__serial_number",
        "truck__make",
        "truck__model",
        "company_rel__name",
    )
    list_filter = (
        ("truck", DALFRelatedFieldAjax),
        "type_category",
        "region",
        "agency",
        # "company",
        "company_rel",
    )
    autocomplete_fields = ("truck", "crew_boss_primary", "crew_boss_alternate", "crew_boss_alternate_2")

    list_display_links = ("updated_at",)

    @admin.display(description="Dispatches")
    def get_dispatches(self, obj):
        dispatches = obj.dispatch_entries.all()
        if not dispatches.exists():
            return "-"
        return format_html(
            "<ul style='margin: 0; padding-left: 1.2em; list-style-type: disc;'>{}</ul>",
            format_html_join("", "<li style='margin-bottom: 4px'>{}</li>", ((str(d),) for d in dispatches))
        )

    list_display = (
        # "__str__",
        "updated_at",
        "get_dispatches",
        # "firecrew",
        "truck",
        "crew_boss_primary",
        "crew_boss_alternate",
        "crew_boss_alternate_2",
        # "company",
        "company_rel",
        "number",
        "award_number",
        "resource_number",
        "type_category",
        "type_number",
        "dispatch_address",
        "region",
        "agency",
        "rate",
        "per_dof_hr",
        "expiration_date",
        "award_sheet_file",
        "full_contract",
        # "created_at",
    )
    list_editable = (
        # "firecrew",
        "truck",
        "crew_boss_primary",
        "crew_boss_alternate",
        "crew_boss_alternate_2",
        # "company",
        "company_rel",
        "number",
        "award_number",
        "resource_number",
        "type_category",
        "type_number",
        "dispatch_address",
        "region",
        "agency",
        "rate",
        "per_dof_hr",
        "expiration_date",
        # "award_sheet_file",
        # "full_contract",
    )
    ordering = ("-updated_at",)

    fields = (
        # "dispatches",
        # "firecrew",
        "truck",
        "crew_boss_primary",
        "crew_boss_alternate",
        "crew_boss_alternate_2",
        # "company",
        "company_rel",
        "number",
        "award_number",
        "resource_number",
        "type_category",
        "type_number",
        "dispatch_address",
        "region",
        "agency",
        "rate",
        "per_dof_hr",
        "expiration_date",
        "award_sheet_file",
        "full_contract",
        ("created_at", "updated_at"),
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = [DispatchInline]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        for name in ("truck",):
            f = form.base_fields.get(name)
            if not f:
                continue
            w = f.widget
            if isinstance(w, RelatedFieldWidgetWrapper):
                w.can_delete_related = False  # убираем опасный крестик удаления

        return form

    class Media:
        css = {
            "all": (
                "core/DALFRelatedFieldAjax.css",
                # "grappelli/css/admin_breadcrumbs.css",
            )
        }
        js = (
            # "grappelli/js/admin_breadcrumbs.js",
        )
