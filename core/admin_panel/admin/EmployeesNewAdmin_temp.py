from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminDateWidget
from django.utils.text import slugify
from django.db.models import Prefetch
from django_admin_flexlist import FlexListAdmin

# from django.db.models import OuterRef, Subquery, CharField, Prefetch

from company.models.Employees import *
from company.models.EmployeesParameters import Employees_Parameters
from exchange.models import Contacts_Prop


class EmployeesParametersInline(admin.TabularInline):  # admin.StackedInline
    def has_add_permission(self, request, obj=None):
        return False

    model = Employees_Parameters
    fields = (
        "contacts_prop",
        "value",
        "updated_at",
    )
    readonly_fields = (
        "contacts_prop",
        "value",
        "updated_at",
    )
    extra = 0
    can_delete = False
    ordering = ("-updated_at",)


# ----------------------------
# ----------------------------
class ParameterForm(forms.ModelForm):
    class Meta:
        model = Employees_Parameters
        fields = ["value"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, "instance", None)

        if instance and getattr(instance, "contacts_prop", None):
            prop = instance.contacts_prop
            self.fields["value"].label = prop.property_name

            if prop.property_type == Contacts_Prop.TypeChoices.SYSTEM_TIME:
                fmt = prop.datetime_format or "%m/%d/%Y"
                self.fields["value"].widget = AdminDateWidget(format=fmt) #AdminSplitDateTime AdminSplitDateTime

                # 👇 подменяем initial value, если есть value_date
                if instance.value_date:
                    self.initial["value"] = instance.value_date.strftime(
                        prop.datetime_format or "%m/%d/%Y"
                    )


# ----------------------------
# 1. Driver's License
# ----------------------------
class DriverLicenseParametersInline(admin.TabularInline):
    model = Employees_Parameters
    form = ParameterForm
    extra = 0
    can_delete = False
    verbose_name_plural = "Driver's License"

    FIELDS = [
        "Driver's License Issue Date",
        "Driver's License Expiration Date",
        "Driver's License State, Number",
        "Driver's License Endorsements",
        "Driver's License Restrictions",
    ]

    def get_formset(self, request, obj=None, **kwargs):
        if obj:
            self.ensure_dl_params_exist(obj)
        return super().get_formset(request, obj, **kwargs)

    def ensure_dl_params_exist(self, employee):
        from exchange.models import Contacts_Prop

        existing_props = set(
            Employees_Parameters.objects.filter(
                employee=employee,
                contacts_prop__property_name__in=self.FIELDS
            ).values_list("contacts_prop__property_name", flat=True)
        )

        missing = set(self.FIELDS) - existing_props

        for prop_name in missing:
            try:
                prop = Contacts_Prop.objects.get(property_name=prop_name)
                Employees_Parameters.objects.create(
                    employee=employee,
                    contacts_prop=prop,
                    value=""
                )
            except Contacts_Prop.DoesNotExist:
                continue

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("contacts_prop").filter(
            contacts_prop__property_name__in=self.FIELDS
        )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    fields = ["value"]

    template = "admin/edit_inline/custom_tabular.html"



# ----------------------------
# 2. Passport
# ----------------------------
class PassportParametersInline(admin.TabularInline):
    model = Employees_Parameters
    form = ParameterForm
    extra = 0
    can_delete = False
    verbose_name_plural = "Passport"

    FIELDS = [
        "Passport Number",
        "Passport Expiration Date",
    ]

    def get_formset(self, request, obj=None, **kwargs):
        if obj:
            self.ensure_params_exist(obj)
        return super().get_formset(request, obj, **kwargs)

    def ensure_params_exist(self, employee):
        from exchange.models import Contacts_Prop

        existing_props = set(
            Employees_Parameters.objects.filter(
                employee=employee,
                contacts_prop__property_name__in=self.FIELDS
            ).values_list("contacts_prop__property_name", flat=True)
        )

        missing = set(self.FIELDS) - existing_props

        for prop_name in missing:
            try:
                prop = Contacts_Prop.objects.get(property_name=prop_name)
                Employees_Parameters.objects.create(
                    employee=employee,
                    contacts_prop=prop,
                    value=""
                )
            except Contacts_Prop.DoesNotExist:
                continue

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("contacts_prop").filter(
            contacts_prop__property_name__in=self.FIELDS
        )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    fields = ["value"]

    template = "admin/edit_inline/custom_tabular.html"



@admin.register(ContactsExchange)
class EmployeesNewAdmin_temp(FlexListAdmin):
    def has_delete_permission(self, request, obj=None):
        return False

    search_fields = ("id", "email", "contact_id", "test")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            Prefetch(
                "employees_parameters_entries",
                queryset=Employees_Parameters.objects.select_related("contacts_prop"),
                to_attr="cached_parameters"
            )
        )
        # Это для сортировки
        # qs = EmployeesNew.objects.prefetch_related(
        #     Prefetch(
        #         "employees_parameters_entries",
        #         queryset=Employees_Parameters.objects.select_related("contacts_prop"),
        #         to_attr="cached_parameters"
        #     )
        # )
        # param_names = Contacts_Prop.objects.filter(
        #     visibility=True, param_mirror=False
        # ).values_list("property_name", flat=True)
        #
        # annotations = {}
        # for param_name in param_names:
        #     field_alias = f"cached_{slugify(param_name).replace('-', '_')}"
        #     subquery = Employees_Parameters.objects.filter(
        #         employee=OuterRef("pk"),
        #         contacts_prop__property_name=param_name
        #     ).values("value")[:1]
        #
        #     annotations[field_alias] = Subquery(subquery, output_field=CharField())
        #
        # qs = qs.annotate(**annotations)
        #
        # return qs.annotate(**annotations)

    def get_dynamic_fields(self):
        param_names = Contacts_Prop.objects.filter(
            visibility=True,
        ).values_list("property_name", flat=True)

        dynamic_fields = []
        for param_name in param_names:
            field_name = f"param_{slugify(param_name).replace('-', '_')}"

            if hasattr(self.__class__, field_name):
                dynamic_fields.append(field_name)
                continue

            def make_func(param_name):
                def _func(self, obj):
                    for param in getattr(obj, "cached_parameters", []):
                        if param.contacts_prop.property_name == param_name:
                            return param.value
                    return "-"

                _func.short_description = param_name
                # Для сортировки
                # _func.admin_order_field = f"cached_{slugify(param_name).replace('-', '_')}"
                return _func

            setattr(self.__class__, field_name, make_func(param_name))
            dynamic_fields.append(field_name)

        return dynamic_fields

    def get_list_display(self, request):
        """Формирует list_display, добавляя динамические поля с сортировкой."""
        base_fields = (
            "email",
            "contact_id",
            "phone",
            "first_name",
            "middle_name",
            "last_name",
            "job_title",
            "last_modified_name",
            "last_modified_time",
            "datetime_created",
            "updated_at",
            "test",
        )
        return list(base_fields) + self.get_dynamic_fields()
        # Для сортировки
        # return list(base_fields) + list(self.get_dynamic_fields())

    def changelist_view(self, request, extra_context=None):
        """Обновляет list_display перед рендерингом списка записей."""
        self.list_display = self.get_list_display(request)
        return super().changelist_view(request, extra_context)


    def get_inline_instances(self, request, obj=None):
        instances = super().get_inline_instances(request, obj)
        for inline in instances:
            if isinstance(inline, DriverLicenseParametersInline):
                inline._custom_context = {"aaa": "bbb"}  # 👈 твоя переменная
        return instances

    inlines = (
        DriverLicenseParametersInline,
        PassportParametersInline,
        EmployeesParametersInline,
    )

    # list_filter = ("status_code", "email")
    # list_filter = ("status_code",)
    # class Media:
    #     css = {
    #         "all": ("core/custom_inline.css",)
    #     }
    #     js = ("core/custom_inline.js",)
