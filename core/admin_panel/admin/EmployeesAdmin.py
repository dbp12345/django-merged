import re
from datetime import date

from dal import autocomplete
from django import forms
from django.conf import settings
from django.contrib import admin

# from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
# from django.contrib.admin.widgets import AdminDateWidget, AdminFileWidget, AdminRadioSelect
# from django.core.files.uploadedfile import UploadedFile
from django.db.models import Case, Count, IntegerField, Prefetch, Q, When
from django.db import transaction
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django_admin_flexlist import FlexListAdmin

from company.models import Employees_Parameters, Employees_Pictures
from company.models.Employees import (
    Availability,
    Course,
    DispatchingStatus,
    Draws,
    Employees,
    EmergencyContact,
    FireRun,
    Interaction,
    NomexCheckOut,
    NomexCheckIn,
    RateOfPay,
    Student,
    Tag,
    TaskBook,
    Notes,
)
from company.services import EmployeesService
from core.models.admin_config import ConfigurableInlineMixin
from core.resolve_param_behavior import resolve_param_behavior
from exchange.models import Contacts_Prop
from paychex.models import Paycheck
from pdf_plugin.admin_mixin import PDFGenerateMixin

SPECIAL_USERS_SET = {u.strip().lower() for u in settings.SPECIAL_USERS}


# from django.db.models import Case, When

# ----------------------------
# class ParameterForm(forms.ModelForm):
#     correcting_errors_in_exchange_to_date_type = [
#         "ETA, Late, Dispatch",
#         "Driver's License Issue Date",
#         "Driver's License Expiration Date",
#     ]
#     CHOICE_FIELDS = {
#         "Availability status": AVAILABILITY_STATUS,
#         "Dispatch Call Status": [(status.label, status.label) for status in DispatchStatus],
#         "Type of interaction": INTERACTION_STATUS,
#     }
#
#     class Meta:
#         model = Employees_Parameters
#         fields = ["value", "value_file"]
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         instance = getattr(self, "instance", None)
#
#         if instance and getattr(instance, "contacts_prop", None):
#             prop = instance.contacts_prop
#
#             if "value" in self.fields:
#                 self.fields["value"].label = prop.property_name
#
#             if prop.property_name in self.CHOICE_FIELDS:
#                 self.fields["value"] = forms.ChoiceField(
#                     choices=self.CHOICE_FIELDS[prop.property_name],
#                     required=False,
#                     label=prop.property_name,
#                 )
#             elif prop.property_type == Contacts_Prop.TypeChoices.SYSTEM_TIME
#             or prop.property_name in self.correcting_errors_in_exchange_to_date_type:
#                 fmt = prop.datetime_format or "%m/%d/%Y"
#                 if "value" in self.fields:
#                     self.fields["value"].widget = AdminDateWidget(format=fmt)
#                 if instance.value_date:
#                     self.initial["value"] = instance.value_date.strftime(fmt)
#             elif prop.property_type == Contacts_Prop.TypeChoices.BOOL:
#                 if "value" in self.fields:
#                     self.fields["value"].widget = forms.CheckboxInput()
#                 self.initial["value"] = instance.value_bool
#             elif prop.property_type == Contacts_Prop.TypeChoices.DOCUMENT:
#                 if "value" in self.fields:
#                     self.fields["value"].widget = AdminFileWidget()
#                 if instance.value_file:
#                     self.initial["value"] = instance.value_file
#
#     def clean(self):
#         cleaned_data = super().clean()
#         instance = self.instance
#         prop = instance.contacts_prop if instance else None
#
#         if prop and prop.property_type == Contacts_Prop.TypeChoices.DOCUMENT:
#             upload = self.files.get(self.add_prefix("value"))
#             if isinstance(upload, UploadedFile):
#                 instance.value_file = upload
#                 # cleaned_data["value"] = upload  # если хочешь сохранять имя файла
#         if prop and prop.property_type == Contacts_Prop.TypeChoices.BOOL:
#             val = bool(cleaned_data.get("value") in [True, "True", "true", "on", 1])
#             cleaned_data["value"] = "True" if val else "False"
#             instance.value_bool = bool(val)
#
#         return cleaned_data


# # ----------------------------
# # 0. Base
# # ----------------------------
# class BaseEmployeeParameterInline(admin.TabularInline):
#     model = Employees_Parameters
#     form = ParameterForm
#     extra = 0
#     can_delete = False
#     verbose_name_plural = "Base"
#
#     FIELDS = []
#
#     def get_formset(self, request, obj=None, **kwargs):
#         if obj:
#             self.ensure_params_exist(obj)
#         return super().get_formset(request, obj, **kwargs)
#
#     def ensure_params_exist(self, employee):
#         from exchange.models import Contacts_Prop
#
#         existing_props = set(
#             Employees_Parameters.objects.filter(
#                 employee=employee,
#                 contacts_prop__property_name__in=self.FIELDS
#             ).values_list("contacts_prop__property_name", flat=True)
#         )
#
#         missing = set(self.FIELDS) - existing_props
#
#         for prop_name in missing:
#             try:
#                 prop = Contacts_Prop.objects.get(property_name=prop_name)
#                 Employees_Parameters.objects.create(
#                     employee=employee,
#                     contacts_prop=prop,
#                     value=""
#                 )
#             except Contacts_Prop.DoesNotExist:
#                 continue
#
#     def get_queryset(self, request):
#         qs = super().get_queryset(request).select_related("contacts_prop").filter(
#             contacts_prop__property_name__in=self.FIELDS
#         )
#
#         whens = [When(contacts_prop__property_name=name, then=pos) for pos, name in enumerate(self.FIELDS)]
#         return qs.order_by(Case(*whens))
#
#     def has_add_permission(self, request, obj=None):
#         return False
#
#     def has_delete_permission(self, request, obj=None):
#         return False
#
#     def get_readonly_fields(self, request, obj=None):
#         return self.fields  # автоматически делает все поля read-only
#
#     fields = ["value"]
#
#     template = "admin/edit_inline/custom_tabular.html"


# # ----------------------------
# #  DriverLicenseParameters
# # ----------------------------
# class DriverLicenseParametersInline(BaseEmployeeParameterInline):
#     verbose_name_plural = "Driver's License"
#     FIELDS = [
#         "Driver's License Issue Date",
#         "Driver's License Expiration Date",
#         "Driver's License State, Number",
#         "Driver's License Endorsements",
#         "Driver's License Restrictions",
#     ]


# # ----------------------------
# #  PassportParameters
# # ----------------------------
# class PassportParametersInline(BaseEmployeeParameterInline):
#     verbose_name_plural = "Passport"
#     FIELDS = [
#         "Passport Number",
#         "Passport Expiration Date",
#     ]


# # ----------------------------
# #  SsnParameters
# # ----------------------------
# class SsnParametersInline(BaseEmployeeParameterInline):
#     verbose_name_plural = "Social Security Number"
#     FIELDS = [
#         "Social Security Number",
#     ]


# # ----------------------------
# #  MedicalCardParameters
# # ----------------------------
# class MedicalCardParametersInline(BaseEmployeeParameterInline):
#     verbose_name_plural = "Medical Card"
#     FIELDS = [
#         "Medical Card Expiration Date",
#     ]


# # ----------------------------
# #  AvailabilityParameters
# # ----------------------------
# class AvailabilityParametersInline(BaseEmployeeParameterInline):
#     verbose_name_plural = "Availability"
#     FIELDS = [
#         "Availability status",
#         "Date of change",
#         "Date of expected future change",
#         "Current State Dispatching From",
#         "Current City Dispatching From",
#         "Travel Time",
#         "Availability notes",
#     ]
#     # ParameterForm.CHOICE_FIELDS = {
#     #     "Availability status": AVAILABILITY_STATUS,
#     # }


# # ----------------------------
# #  DispatchingStatusParameters
# # ----------------------------
# class DispatchingStatusParametersInline(BaseEmployeeParameterInline):
#     verbose_name_plural = "Dispatching statuses"
#     FIELDS = [
#         "Dispatch Status Update Date",
#         "Dispatch Status Update Time",
#         "Dispatch Call Status",
#         "Dispatch Category",
#         "ETA, Late, Dispatch",
#         "Dispatch location",
#         "Dispatch notes",
#     ]
#     # ParameterForm.CHOICE_FIELDS = {
#     #     "Dispatch Call Status": [(status.label, status.label) for status in DispatchStatus],
#     # }


# # ----------------------------
# #  DrugTestParameters
# # ----------------------------
# class DrugTestParametersInline(BaseEmployeeParameterInline):
#     verbose_name_plural = "Drug test"
#     FIELDS = [
#         "Drug Test date",
#         "Drug Test preseason",
#     ]


# # ----------------------------
# #  EmploymentPacketParameters
# # ----------------------------
# class EmploymentPacketParametersInline(BaseEmployeeParameterInline):
#     verbose_name_plural = "Employment Packet"
#     FIELDS = [
#         "Employee Packet",
#         "Current Pack Test Date",
#         "Current Pack Test Date signed",
#         "Pack Test document",
#     ]


# # ----------------------------
# #  InteractionsParameters
# # ----------------------------
# class InteractionsParametersInline(BaseEmployeeParameterInline):
#     verbose_name_plural = "Interactions"
#     FIELDS = [
#         "Type of interaction",
#         "Last Attempted Communication",
#         "Negative interaction",
#         "Interaction notes",
#     ]
#     # ParameterForm.CHOICE_FIELDS = {
#     #     "Type of interaction": INTERACTION_STATUS,
#     # }


# # ----------------------------
# #  IQCCardParameters
# # ----------------------------
# class IQCCardParametersInline(BaseEmployeeParameterInline):
#     verbose_name_plural = "IQC Card"
#     FIELDS = [
#         "IQC Position",
#         "Packtest Results",
#         "IQC Issue date",
#         "Pack Test document",
#     ]


# # ----------------------------
# #  CompanyManifestParameters
# # ----------------------------
# class CompanyManifestParametersInline(BaseEmployeeParameterInline):
#     verbose_name_plural = "Manifest"
#     FIELDS = [
#         "Manifest Date, 2025",
#         "Manifest Date, 2024",
#         "Manifest Date, 2023",
#         "Manifest Date, 2022",
#         "Manifest Date, 2021",
#         "Manifest Date",
#     ]


# # ----------------------------
# #  MSPAParameters
# # ----------------------------
# class MSPAParametersInline(BaseEmployeeParameterInline):
#     verbose_name_plural = "MSPA"
#     FIELDS = [
#         "MSPA Issue date",
#         "MSPA Expiration Date",
#         "MSPA Number",
#         "MSPA document",
#     ]


# admin.StackedInline
# admin.TabularInline

# class EmployeesParametersInline(admin.TabularInline):
#     def has_add_permission(self, request, obj=None):
#         return False
#
#     def get_queryset(self, request):
#         qs = super().get_queryset(request)
#         return qs.exclude(contacts_prop__param_mirror=True).filter(contacts_prop__property_name="text_body")
#
#     model = Employees_Parameters
#     fields = (
#         # "contacts_prop",
#         "value",
#     )
#     readonly_fields = (
#         # "contacts_prop",
#         "value",
#     )
#     extra = 0
#     can_delete = False
#     # ordering = ("-updated_at",)


class EmployeesPicturesInline(admin.TabularInline):
    # def has_add_permission(self, request, obj=None):
    #     return False

    model = Employees_Pictures
    fields = (
        (
            "photo_privser_picture_at_field_training_preview",
            "photo_privser_picture_at_field_training",
        ),
        (
            "photo_privser_cropped_picture_for_red_card_preview",
            "photo_privser_cropped_picture_for_red_card",
        ),
        # ("photo_privser_passport_picture_preview", "photo_privser_passport_picture"),
    )
    readonly_fields = (
        "photo_privser_picture_at_field_training_preview",
        "photo_privser_cropped_picture_for_red_card_preview",
        # "photo_privser_passport_picture_preview",
    )
    extra = 0
    can_delete = True
    # ordering = ()


class EmergencyContactInline(ConfigurableInlineMixin, admin.TabularInline):
    # def has_add_permission(self, request, obj=None):
    #     return False

    model = EmergencyContact
    fk_name = "employee"
    fields = (
        "type",
        "relation_to_you",
        "is_primary",
        "relationship",
    )
    readonly_fields = ("relationship",)
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)


# class MSPAInline(admin.TabularInline):
#     # def has_add_permission(self, request, obj=None):
#     #     return False
#
#     model = MSPA
#     fields = (
#         "issue_date",
#         "expiration_date",
#         "MSPA_number",
#         # "document",
#         "document_preview",
#     )
#     readonly_fields = (
#         "document_preview",
#     )
#     extra = 0
#     can_delete = True
#     show_change_link = True
#     ordering = ("-updated_at",)


# class IdentificationDocumentsInline(admin.TabularInline):
#     # def has_add_permission(self, request, obj=None):
#     #     return False
#
#     model = IdentificationDocuments
#     fields = (
#         "type",
#         "issue_date",
#         "expiration_date",
#         "number",
#         "endorsement",
#         "restriction",
#         # "document",
#         "document_preview",
#         "updated_at",
#     )
#     readonly_fields = (
#         "document_preview",
#         "updated_at",
#     )
#     extra = 0
#     can_delete = True
#     show_change_link = True
#     ordering = ("-updated_at",)


# class DispatchingStatusInline(admin.TabularInline):
#     # def has_add_permission(self, request, obj=None):
#     #     return False
#
#     model = DispatchingStatus
#     fields = (
#         "date",
#         "positive_interaction",
#         "dispatch_status",
#         "dispatch_category",
#         "ETA",
#         "location",
#         "notes",
#     )
#     readonly_fields = (
#     )
#     extra = 0
#     can_delete = True
#     show_change_link = True
#     ordering = ("-updated_at",)


# class CompanyManifestInline(admin.TabularInline):
#     model = CompanyManifest
#     fields = (
#         "date",
#     )
#     readonly_fields = (
#     )
#     extra = 0
#     can_delete = True
#     show_change_link = True
#     ordering = ("-updated_at",)


# class DrugTestInline(admin.TabularInline):
#     model = DrugTest
#     fields = (
#         "date",
#         "result",
#     )
#     readonly_fields = (
#     )
#     extra = 0
#     can_delete = True
#     show_change_link = True
#     ordering = ("-updated_at",)


class NomexCheckOutInline(ConfigurableInlineMixin, admin.TabularInline):
    model = NomexCheckOut
    fields = (
        "date",
        "pants_serial_number",
        "shirt_serial_number",
    )
    readonly_fields = ()
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)


class NomexCheckInInline(ConfigurableInlineMixin, admin.TabularInline):
    model = NomexCheckIn
    fields = (
        "date",
        "pants_serial_number",
        "shirt_serial_number",
    )
    readonly_fields = ()
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)


# class EmploymentPacketInline(admin.TabularInline):
#     model = EmploymentPacket
#     fields = (
#         "packet_name",
#         "date_sent",
#         "date_signed",
#         # "document",
#         "document_preview",
#     )
#     readonly_fields = (
#         "document_preview",
#     )
#     extra = 0
#     can_delete = True
#     show_change_link = True
#     ordering = ("-updated_at",)


# class IQCCardInline(admin.TabularInline):
#     model = IQCCard
#     fields = (
#         "position",
#         "pack_test",
#         "date",
#         "document",
#     )
#     readonly_fields = (
#     )
#     extra = 0
#     can_delete = True
#     show_change_link = True
#     ordering = ("-updated_at",)


# class InteractionInline(admin.TabularInline):
#     model = Interaction
#     fields = (
#         "type_of_interaction",
#         "date",
#         "negative_interaction",
#         "notes",
#     )
#     readonly_fields = (
#     )
#     extra = 0
#     can_delete = True
#     show_change_link = True
#     ordering = ("-updated_at",)


class TaskBookInline(ConfigurableInlineMixin, admin.TabularInline):
    model = TaskBook
    fields = (
        "type_of_taskbook",
        "initiated_date",
        "completed_date",
        "updated_date",
        "final_evaluator",
        "document_preview",
        "document",
    )
    readonly_fields = ("document_preview",)
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)


class NotesInline(ConfigurableInlineMixin, admin.TabularInline):
    model = Notes
    fields = ("body",)
    readonly_fields = ()
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)


# class AvailabilityInline(admin.TabularInline):
#     model = Availability
#     extra = 0
#     can_delete = True
#     show_change_link = True
#     ordering = ("-updated_at",)
#     readonly_fields = (
#     )
#
#     fields = (
#         "availability_status",
#         "date_of_change",
#         "date_of_expected_future_change",
#         "location_state",
#         "location_city",
#         "travel_time",
#         "notes",
#     )


# class CurrentAssignedInline(admin.TabularInline):
#     model = CurrentAssigned
#     fields = (
#         "date",
#     )
#     readonly_fields = (
#     )
#     extra = 0
#     can_delete = True
#     show_change_link = True
#     ordering = ("-updated_at",)


class CourseInline(ConfigurableInlineMixin, admin.TabularInline):
    model = Course
    fields = (
        "training_type",
        "inperson_required",
        "governing_body",
    )
    readonly_fields = ()
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)


# class TrainingClassInline(admin.TabularInline):
#     model = TrainingClass
#     # fk_name = "employee"
#     fields = (
#         "instructor",
#         "course",
#         "test_score",
#         "date",
#         "location",
#         # "document",
#         "document_preview",
#     )
#     readonly_fields = (
#         "document_preview",
#     )
#     extra = 0
#     can_delete = True
#     show_change_link = True
#     ordering = ("-updated_at",)


class StudentInline(ConfigurableInlineMixin, admin.TabularInline):
    model = Student
    autocomplete_fields = ("training_class",)
    fields = (
        # "get_training_type_name",
        "training_class",
        "test_score",
        "verified",
        # "certificate_confirmed",
        "document",
        "document_preview",
    )
    readonly_fields = (
        # "get_training_type_name",
        # "training_class",
        "document_preview",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("training_class__course__training_type__name", "-training_class__date")

    # def has_add_permission(self, request, obj=None):
    #     return False

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("training_class__course__training_type")
        )

    @admin.display(description="Course Type")
    def training_class_type(self, obj):
        if obj.training_class and obj.training_class.course:
            return obj.training_class.course.training_type.name
        return "-"

    @admin.display(description="Course Name")
    def course_name(self, obj):
        if obj.training_class and obj.training_class.course:
            return obj.training_class.course.name
        return "-"


class RateOfPayInline(ConfigurableInlineMixin, admin.TabularInline):
    model = RateOfPay
    fields = (
        "base_rate",
        "bonus_rate",
        "office_rate",
        "year",
        "date",
    )
    readonly_fields = ()
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)


# class FireInline(admin.TabularInline):
#     model = Fire
#     fields = (
#         "fire_number",
#         "incident_name",
#         "incident_type",
#         "fuel_type",
#         # "reliability_leaving",
#         "agency",
#         "state",
#     )
#     readonly_fields = (
#     )
#     extra = 0
#     can_delete = True
#     show_change_link = True
#     ordering = ("-updated_at",)


class FireRunInline(ConfigurableInlineMixin, admin.TabularInline):
    model = FireRun
    fk_name = "employee"
    extra = 0
    can_delete = False
    show_change_link = True
    ordering = ("-start_date",)

    # @admin.display(description="Crew boss")
    # def filter_list_by_crew_name(self, instance):
    #     crew_crew_name = self.crew_crew_name(instance)
    #     if not crew_crew_name or crew_crew_name == "-":
    #         return "-"
    #     url = reverse("admin:company_crew_change", args=[instance.crew.id])
    #     return format_html('<a href="{}" style="white-space: nowrap !important;"
    # rel="noreferrer noopener">{}</a>', url, crew_crew_name)

    # @admin.display(description="Crew boss")
    # def crwb_link_to_firerun(self, instance):
    #     url = reverse("admin:company_firerun_change", args=[instance.id])
    #     return format_html('<a href="{}" style="white-space: nowrap !important;"
    # rel="noreferrer noopener">{}</a>', url, instance.crwb or "-")

    @admin.display(description="")
    def arrow_to_firerun(self, instance):
        url = reverse("admin:company_firerun_change", args=[instance.id])
        return format_html(
            '<a href="{}" class="grp-edit-link-arrow" title="Change">➜</a>',
            url,
        )

    @admin.display(description="Incident date")
    def start_date_link_to_firerun(self, instance):
        url = reverse("admin:company_firerun_change", args=[instance.id])
        return format_html(
            '<a href="{}" style="white-space: nowrap !important;" rel="noreferrer noopener">{}</a>',
            url,
            instance.start_date.strftime("%m/%d/%Y") or "-",
        )

    fields = (
        "arrow_to_firerun",
        "start_date_link_to_firerun",
        "start_date",
        "job_title",
        "crew_fire_activity_code",
        "crew_fire_agency",
        "crew_fire_state",
        "operational_periods",
        "crew_fire_incident_type",
        "crew_fire_fuel_type",
        "crew_fire_fire_size",
        "crew_fire_incident_name",
        # "crew_crew_name",
        # "filter_list_by_crew_name",
        "crwb",
        # "crwb_link_to_firerun",
        "hotline_shifts",
        "eval_hotline",
        "hotline_in_remarks",
        "rating",
        "ranking",
        "task_book",
    )
    readonly_fields = (
        "arrow_to_firerun",
        "start_date_link_to_firerun",
        "start_date",
        "job_title",
        "crew_fire_activity_code",
        "crew_fire_agency",
        "crew_fire_state",
        "operational_periods",
        "crew_fire_incident_type",
        "crew_fire_fuel_type",
        "crew_fire_fire_size",
        "crew_fire_incident_name",
        # "crew_crew_name",
        # "filter_list_by_crew_name",
        "crwb",
        # "crwb_link_to_firerun",
        "hotline_shifts",
        "eval_hotline",
        "hotline_in_remarks",
        "task_book",
        # "rating",
        # "ranking",
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("crew", "crew__fire")

    @admin.display(description="Crew boss")
    def crew_crew_name(self, instance):
        return instance.crew.crew_name if instance.crew else "-"

    @admin.display(description="Agency")
    def crew_fire_agency(self, instance):
        fire = instance.crew.fire if instance.crew and instance.crew.fire else None
        return fire.agency if fire else "-"

    @admin.display(description="State")
    def crew_fire_state(self, instance):
        fire = instance.crew.fire if instance.crew and instance.crew.fire else None
        return fire.state if fire else "-"

    @admin.display(description="Fire Number")
    def crew_fire_fire_number(self, instance):
        fire = instance.crew.fire if instance.crew and instance.crew.fire else None
        return fire.fire_number if fire else "-"

    @admin.display(description="Level")  # Management Type or Complexity Level
    def crew_fire_incident_type(self, instance):
        fire = instance.crew.fire if instance.crew and instance.crew.fire else None
        return fire.incident_type if fire else "-"

    @admin.display(description="Incident Name")
    def crew_fire_incident_name(self, instance):
        fire = instance.crew.fire if instance.crew and instance.crew.fire else None
        return fire.incident_name if fire else "-"

    @admin.display(description="Fuel type")
    def crew_fire_fuel_type(self, instance):
        fire = instance.crew.fire if instance.crew and instance.crew.fire else None
        return fire.fuel_type if fire else "-"

    @admin.display(description="Fire size")
    def crew_fire_fire_size(self, instance):
        fire = instance.crew.fire if instance.crew and instance.crew.fire else None
        return fire.fire_size if fire else "-"

    @admin.display(description="Activity code")
    def crew_fire_activity_code(self, instance):
        fire = instance.crew.fire if instance.crew and instance.crew.fire else None
        return fire.activity_code if fire else "-"


class DrawsInline(ConfigurableInlineMixin, admin.TabularInline):
    model = Draws
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)
    readonly_fields = ()

    fields = (
        "date",
        "type",
        "amount",
        "signature",
        "payer",
    )


class PayInline(ConfigurableInlineMixin, admin.TabularInline):
    model = Draws
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)
    readonly_fields = ()

    fields = (
        "date",
        "type",
        "amount",
        "signature",
        "payer",
    )


class EmployeesStateFilter(admin.SimpleListFilter):
    title = "Type"
    parameter_name = "type"

    def lookups(self, request, model_admin):
        types = Employees.objects.values("type").annotate(count=Count("type"))
        return [
            (
                employee_type["type"],
                f"{employee_type['type']} ({employee_type['count']})",
            )
            for employee_type in types
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(type=self.value())
        return queryset


def crew_list_display(obj):
    if not obj.fire_crew:
        return "No crew assigned"
    return f"<b>{obj.fire_crew.name}</b>"


def get_employee_params_dict(employee, params):
    # param_dict = {p.contacts_prop.id: p.value for p in getattr(employee, "parameters", [])}
    # param_dict = {
    #     p.contacts_prop.id: (
    #         p.value_bool if p.contacts_prop.property_type == Contacts_Prop.TypeChoices.BOOL else p.value
    #     )
    #     for p in getattr(employee, "parameters", [])
    # }

    param_dict = {}
    for p in getattr(employee, "parameters", []):
        if p.contacts_prop.property_type == Contacts_Prop.TypeChoices.BOOL:
            param_dict[p.contacts_prop.id] = p.value_bool
        elif p.contacts_prop.property_type == Contacts_Prop.TypeChoices.SYSTEM_TIME:
            param_dict[p.contacts_prop.id] = (
                p.value_date.strftime("%m/%d/%Y") if p.value_date else None
            )
        else:
            param_dict[p.contacts_prop.id] = p.value
    return {param: param_dict.get(param[0], "") for param in params}


def get_grouped_parameters(
    employee, field_groups: dict, extra_html_blocks: dict = None
):
    # Универсально: поддержка tuple/list как "ряд", плюс trim имён.
    from company.models import Employees_Parameters
    from exchange.models import Contacts_Prop

    def norm_name(x):
        return x.strip() if isinstance(x, str) else x

    # кэш существующих значений по нормализованным именам
    all_params = {
        norm_name(p.contacts_prop.property_name): (p.contacts_prop, p)
        for p in employee.employees_parameters_entries.select_related("contacts_prop")
    }

    # собрать недостающие имена
    needed = set()
    for items in field_groups.values():
        for it in items:
            if isinstance(it, (list, tuple)):
                for name in it:
                    n = norm_name(name)
                    if n not in all_params:
                        needed.add(n)
            else:
                n = norm_name(it)
                if n not in all_params:
                    needed.add(n)

    # оптом подтянуть недостающие Contacts_Prop
    props_by_name = {
        norm_name(p.property_name): p
        for p in Contacts_Prop.objects.filter(property_name__in=needed)
    }

    def build_field(raw_name):
        # Special marker for empty field (used to align table columns)
        if raw_name is None:
            return {
                "name": "",
                "id": "",
                "value": "",
                "is_checkbox": False,
                "is_date": False,
                "is_file": False,
                "choices": None,
                "widget_html": "",
            }
        name = norm_name(raw_name)
        pair = all_params.get(name)
        if pair:
            prop, instance = pair
        else:
            prop = props_by_name.get(name)
            if not prop:
                return None
            instance = Employees_Parameters(
                employee=employee,
                contacts_prop=prop,
                value="",
                value_date=None,
                value_bool=False,
            )
        return resolve_param_behavior(prop, instance)

    result = {}
    for group_name, items in field_groups.items():
        rows = []  # список рядов: [[field, field], [field], ...]
        fields = []  # плоский список для старых шаблонов

        for it in items:
            if isinstance(it, (list, tuple)):
                row = []
                for name in it:
                    f = build_field(name)
                    # Always add field, even if it's empty (None marker)
                    if f is not None:
                        row.append(f)
                        fields.append(f)
                if row:
                    rows.append(row)
            else:
                f = build_field(it)
                # Always add field, even if it's empty (None marker)
                if f is not None:
                    rows.append([f])
                    fields.append(f)

        if rows or fields:
            result[group_name] = {
                "rows": rows,
                "fields": fields,
                "html": (extra_html_blocks or {}).get(group_name, ""),
            }

    return result


# def get_grouped_parameters_v1(employee, field_groups: dict, extra_html_blocks: dict = None):
#     from company.models import Employees_Parameters
#     from exchange.models import Contacts_Prop
#
#     result = {}
#
#     # Кэш всех параметров с привязанными пропами
#     all_params = {
#         p.contacts_prop.property_name: (p.contacts_prop, p)
#         for p in employee.employees_parameters_entries.select_related("contacts_prop")
#     }
#
#     for group_name, property_names in field_groups.items():
#         group_fields = []
#
#         for prop_name in property_names:
#             if prop_name in all_params:
#                 prop, instance = all_params[prop_name]
#             else:
#                 try:
#                     prop = Contacts_Prop.objects.get(property_name=prop_name)
#                     instance = Employees_Parameters(
#                         employee=employee,
#                         contacts_prop=prop,
#                         value="",
#                         value_date=None,
#                         value_bool=False,
#                     )
#                 except Contacts_Prop.DoesNotExist:
#                     continue  # игнорируем несуществующие поля
#
#             data = resolve_param_behavior(prop, instance)
#             group_fields.append(data)
#
#         if group_fields:
#             result[group_name] = {
#                 "fields": group_fields,
#                 "html": extra_html_blocks.get(group_name) if extra_html_blocks else ""
#             }
#
#     return result
#
#
# def get_grouped_parameters_v2(employee, field_groups: dict, extra_html_blocks: dict = None):
#     # Changed: support tuples/lists in FIELDS as a single horizontal row
#     from company.models import Employees_Parameters
#     from exchange.models import Contacts_Prop
#
#     def build_field(prop_name):
#         """Return normalized field dict for a single property_name or None if missing."""
#         # unchanged logic, just wrapped
#         pair = all_params.get(prop_name)
#         if pair:
#             prop, instance = pair
#         else:
#             try:
#                 prop = props_by_name[prop_name]
#             except KeyError:
#                 return None
#             instance = Employees_Parameters(
#                 employee=employee,
#                 contacts_prop=prop,
#                 value="",
#                 value_date=None,
#                 value_bool=False,
#             )
#         return resolve_param_behavior(prop, instance)
#
#     result = {}
#
#     # prefetch everything to avoid N+1
#     all_params = {
#         p.contacts_prop.property_name: (p.contacts_prop, p)
#         for p in employee.employees_parameters_entries.select_related("contacts_prop")
#     }
#     # bulk fetch Contacts_Prop that are missing
#     needed_names = set()
#     for group_items in field_groups.values():
#         for item in group_items:
#             if isinstance(item, (list, tuple)):
#                 needed_names.update(name for name in item if name not in all_params)
#             else:
#                 if item not in all_params:
#                     needed_names.add(item)
#     props_by_name = {
#         p.property_name: p
#         for p in Contacts_Prop.objects.filter(property_name__in=needed_names)
#     }
#
#     for group_name, property_items in field_groups.items():
#         group_rows = []  # list[list[field_dict]]
#         for item in property_items:
#             if isinstance(item, (list, tuple)):
#                 row = [f for name in item if (f := build_field(name)) is not None]
#                 if row:
#                     group_rows.append(row)
#             else:
#                 f = build_field(item)
#                 if f:
#                     group_rows.append([f])  # single field row
#         if group_rows:
#             result[group_name] = {
#                 "rows": group_rows,
#                 "html": extra_html_blocks.get(group_name) if extra_html_blocks else "",
#             }
#     return result


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)


class EmployeesAdminForm(forms.ModelForm):
    class Meta:
        model = Employees
        fields = "__all__"
        widgets = {"tags": autocomplete.ModelSelect2Multiple(url="tag-autocomplete")}


# class TagsThroughInline(admin.TabularInline):
#     model = Employees.tags.through
#     autocomplete_fields = ("tag",)  # можно оставить, но виджет обернём
#     extra = 0
#     can_delete = True
#     show_change_link = False
#
#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         # дебаг — покажет, как зовутся поля through-модели
#         # print("DEBUG through field:", db_field.name, getattr(db_field.remote_field, "model", None))
#         formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
#
#         if db_field.name == "tag":
#             # только если у юзера есть право создавать Tag — тогда + появится
#             app_label = Tag._meta.app_label
#             model_name = Tag._meta.model_name
#             perm = f"{app_label}.add_{model_name}"
#             if request.user.has_perm(perm):
#                 formfield.widget = RelatedFieldWidgetWrapper(
#                     formfield.widget, db_field.remote_field, self.admin_site
#                 )
#         return formfield


class TagsThroughInline(admin.TabularInline):
    model = Employees.tags.through
    extra = 0
    # показываем только вычисляемое поле
    # fields = ("tag_label",)
    # readonly_fields = ("tag_label",)

    # def tag_label(self, obj):
    #     # Предположение: через-модель имеет FK на Tag в поле "tag" (стандарт Django).
    #     # Основание: default Django создаёт поле с именем связанной модели в единственном числе.
    #     tag = getattr(obj, "tag", None)
    #     if tag is None:
    #         # попытки найти по другим именам (на всякий случай)
    #         tag = getattr(obj, "tags", None) or getattr(obj, "tag_id", None)
    #     if not tag:
    #         return "-"
    #     # если получили целый объект Tag — вернём его name, иначе str()
    #     name = getattr(tag, "name", None)
    #     return name if name else str(tag)
    # tag_label.short_description = "Tag"

    # если хочешь удобный выбор — используй raw_id_fields или autocomplete_fields
    # raw_id_fields быстрее, если много тегов:
    # raw_id_fields = ("tag",)
    # или, если настроен TagAdmin.search_fields и хочешь автокомплит:
    autocomplete_fields = ("tag",)
    verbose_name = "Tag"
    verbose_name_plural = "Tags"
    can_delete = True
    show_change_link = False

    # # Запрет на добавление/удаление/изменение через inline
    # def has_add_permission(self, request, obj=None):
    #     return False
    #
    # def has_delete_permission(self, request, obj=None):
    #     return False
    #
    # # Гарантируем, что readonly_fields реально применяются (на будущее)
    # def get_readonly_fields(self, request, obj=None):
    #     return self.readonly_fields


@admin.register(Employees)
class EmployeesAdmin(PDFGenerateMixin, FlexListAdmin):
    # autocomplete_fields = ("tags",)  # удобный многовалентный селектор в форме
    # filter_horizontal = ("tags",)  # удобный многовалентный селектор в форме
    form = EmployeesAdminForm

    def tags_list(self, obj):
        return ", ".join(t.name for t in obj.tags.all())

    tags_list.short_description = "Tags"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_model_perms(self, request):
        return {}

    def changelist_view(self, request, extra_context=None):
        return redirect(reverse("employees_table"))

    # def get_queryset(self, request):
    #     return super().get_queryset(request).prefetch_related(
    #         "emergency_contact_entries",
    #         "mspa_entries",
    #         "identification_documents_entries",
    #         "dispatching_status_entries",
    #         "company_manifest_entries",
    #         "drug_test_entries",
    #         "nomex_checkout_entries",
    #         "nomex_checkin_entries",
    #         "employment_packet_entries",
    #         "IQC_card_entries",
    #         "interaction_entries",
    #         "task_book_entries",
    #         "availability_entries",
    #         "current_assigned_entries",
    #         "training_class_entries_as_instructor",
    #         "student_entries",
    #         "rate_of_pay_entries",
    #         "fire_run_entries",
    #         "draws_entries",
    #     )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Предположение: у тебя связка называется employees_parameters_entries; делаем prefetch для скорости
        return qs.prefetch_related(
            Prefetch("employees_parameters_entries__contacts_prop"),
            Prefetch("tags", queryset=Tag.objects.all()),
        )

    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return super().get_search_results(request, queryset, search_term)

        tokens = [t.strip() for t in re.split(r"[,\s]+", search_term) if t.strip()]

        if not tokens:
            return super().get_search_results(request, queryset, search_term)

        from company.models import Employees_Parameters

        props = ["surname", "given_name", "middle_name", "email"]

        overall_q = Q()
        for token in tokens[:4]:
            sub = Employees_Parameters.objects.filter(
                contacts_prop__property_name__in=props, value__icontains=token
            ).values("employee_id")
            token_q = Q(pk__in=sub) | Q(email__icontains=token)
            overall_q &= token_q

        queryset = queryset.filter(overall_q).distinct()
        return queryset, True

    # def get_search_results22(self, request, queryset, search_term):
    #     if not search_term:
    #         return super().get_search_results(request, queryset, search_term)
    #
    #     q = search_term.strip()
    #     # Список property_name, по которым ищем
    #     props = ["surname", "given_name", "middle_name", "email"]
    #
    #     q_filter = Q()
    #
    #     for prop in props:
    #         q_filter |= Q(
    #             employees_parameters_entries__contacts_prop__property_name=prop,
    #             employees_parameters_entries__value__icontains=q
    #         )
    #
    #     # Дополнительно ищем по реальному полю email (если хочешь)
    #     # q_filter |= Q(email__icontains=q)
    #
    #     queryset = queryset.filter(q_filter).distinct()
    #     return queryset, True

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        if obj:
            self.model._meta.verbose_name = obj.get_file_as or obj.get_email or "-"
        return obj

    inlines = (
        # EmployeesParametersInline,
        # AvailabilityParametersInline, # - new
        # AvailabilityInline, # - old
        # TrainingClassInline, # - old
        # CurrentAssignedInline, # - old
        # DispatchingStatusParametersInline, # - new
        # DispatchingStatusInline, # - old
        # DrugTestParametersInline, # - new
        # DrugTestInline, # - old
        EmergencyContactInline,
        # EmploymentPacketParametersInline, # - new
        # EmploymentPacketInline, # - old
        # DriverLicenseParametersInline, # - new
        # PassportParametersInline, # - new
        # SsnParametersInline, # - new
        # MedicalCardParametersInline, # - new
        # IdentificationDocumentsInline, # - old
        # InteractionsParametersInline, # - new
        # InteractionInline, # - old
        # IQCCardParametersInline, # - new
        # IQCCardInline, # - old
        # CompanyManifestParametersInline, # - new
        # CompanyManifestInline, # - old
        # MSPAParametersInline, # - new
        # MSPAInline, # - old
        NomexCheckInInline,
        NomexCheckOutInline,
        RateOfPayInline,
        StudentInline,
        TaskBookInline,
        # DrawsInline,
        NotesInline,
        EmployeesPicturesInline,
        FireRunInline,
        TagsThroughInline,
    )

    # Заготовка для инлайнов по SPECIAL_USERS
    # def get_inline_instances(self, request, obj=None):
    #     inline_instances = super().get_inline_instances(request, obj)
    #     if obj is None:
    #         return inline_instances  # не показываем в add-view
    #
    #     if request.user.username in SPECIAL_USERS_SET:
    #         if any(isinstance(i, NewInline) for i in inline_instances):
    #             return inline_instances
    #
    #         special = NewInline(self.model, self.admin_site)
    #
    #         for idx, inst in enumerate(inline_instances):
    #             if isinstance(inst, TagsThroughInline):
    #                 inline_instances.insert(idx, special)
    #                 break
    #         else:
    #             inline_instances.append(special)
    #
    #     return inline_instances

    list_per_page = 100
    search_fields = ("email", "id", "tags__name")

    autocomplete_fields = (
        "fire_crew",
        "user",
    )

    # raw_id_fields = ("fire_crew", "user",)

    def paychecks_block_for_admin(self, obj, request, limit=100):
        if not obj or not getattr(obj, "id", None):
            return mark_safe(
                '<div class="grp-group"><h2 class="grp-collapse-handler">No paychecks</h2></div>'
            )
            # return mark_safe("<p>No paychecks (object is new).</p>")

        qs_all = Paycheck.objects.filter(paychex_worker__employees=obj)
        qs = list(qs_all.order_by("-check_date")[:limit])

        if not qs:
            return mark_safe(
                '<div class="grp-group"><h2 class="grp-collapse-handler">Paychecks not found</h2></div>'
            )
            # return mark_safe("<p>Paychecks not found.</p>")

        header = format_html(
            "<tr style='background-image: linear-gradient(#1e4452e3, #405e88e3);color:#eff0e8;'>"
            "<th style='border:none;'>CHECK DATE</th>"
            "<th style='border:none;'>TYPE</th>"
            "<th style='border:none;'>NET</th>"
            "<th style='border:none;'></th>"
            "</tr>"
        )

        def rows():
            for p in qs:
                try:
                    url = reverse(
                        f"admin:{p._meta.app_label}_{p._meta.model_name}_change",
                        args=(p.pk,),
                    )
                except Exception:
                    url = None

                check_date = p.check_date.strftime("%m/%d/%Y") if p.check_date else ""
                check_type = p.check_type or ""
                net = f"{p.net:.2f}" if p.net is not None else ""

                if url:
                    open_link = format_html(
                        '<ul class="grp-tools" style="top:-4px;">'
                        '<li><a href="{}" class="grp-icon grp-edit-link" title="Change"></a></li>'
                        '</ul>',
                        url,
                    )
                else:
                    open_link = "-"

                yield (check_date, check_type, net, open_link)

        body = format_html_join(
            "",
            "<tr><td>{}</td><td>{}</td><td>{}</td><td style='width:1%;'>{}</td></tr>",
            rows(),
        )

        table = format_html(
            '<table class="grp-table" style="width:auto">{}</table>',
            format_html("{}{}", header, body),
        )
        return mark_safe(table)

    @admin.display(description="")
    def show_emp_info(self, obj):
        if not obj.id:
            return ""
        url = reverse("find_by_crwb") + "?" + urlencode({"boss": obj.id})
        return format_html(
            '<span>{}</span><span>{}</span><span>{}</span><span><a href="{}">{}</a></span>',
            obj.get_job_title,
            obj.get_email,
            obj.get_phone,
            url,
            "CRWB Worked With",
        )

    # @admin.display(description="")
    # def pull_link_exc(self, obj):
    #     url = reverse("update_contact_from_exchange_by_email", kwargs={"obj_id": obj.id})
    #     return format_html(
    #         '<a class="button" style="background: var(--button-bg);" href="{}">PULL from Exchange</a>',
    #         url
    #     )

    @admin.display(description="")
    def refresh_link_privser(self, obj):
        url = reverse(
            "update_contact_from_privser_by_email", kwargs={"obj_email": obj.get_email}
        )
        return format_html(
            '<a class="button" style="background: var(--button-bg);" href="{}">PULL from Privser</a>',
            url,
        )

    @admin.display(description="")
    def force_push_link_exc(self, obj):
        url = reverse("contact_forcepush_to_exchange", kwargs={"obj_id": obj.id})
        return format_html(
            '<a class="button" style="background: var(--button-bg);" href="{}">Force PUSH to Exchange</a>',
            url,
        )

    @admin.display(description="")
    def force_push_link_privser(self, obj):
        url = reverse("contact_forcepush_to_privser", kwargs={"obj_id": obj.id})
        return format_html(
            '<a class="button" style="background: var(--button-bg);" href="{}">Force PUSH to Privser</a>',
            url,
        )

    @admin.display(description="")
    def remove_link(self, obj):
        url = reverse("remove_from_system", kwargs={"obj_id": obj.id})
        return format_html(
            '<a class="button" style="color: red" href="{}">Remove</a>', url
        )

    @admin.display(description="Email")
    def short_email(self, obj):
        if len(obj.email) > 36:
            return f"{obj.email[:36]}..."
        return obj.email

    list_display = (
        "short_email",
        "type",
        "crew_list",
        "last_modified_name",
        "last_modified_time",
        "tags_list",
        "updated_at",
        # "pull_link_exc",
        # "force_push_link_exc",
        # "force_push_link_privser",
    )

    def get_list_display(self, request):
        fields = [
            "short_email",
            "type",
            "crew_list",
            "last_modified_name",
            "last_modified_time",
            "tags_list",
            "updated_at",
            # "pull_link_exc",
            # "force_push_link_exc",
            # "force_push_link_privser",
        ]
        if request.user.username in SPECIAL_USERS_SET:
            # fields.append("pull_link_exc")
            fields.append("refresh_link_privser")
            fields.append("force_push_link_exc")
            fields.append("force_push_link_privser")
            fields.append("remove_link")
        return fields

    list_editable = ("type",)
    ordering = ("-last_modified_time",)

    # fields = (
    #     "email",
    #     "pull_link_exc",
    #     "force_push_link_exc",
    #     "force_push_link_privser",
    #     "contact_id",
    #     "type",
    #     "last_modified_name",
    #     "last_modified_time",
    #     ("created_at", "updated_at"),
    # )

    @admin.display(description="Crew")
    def crew_list(self, obj):
        if not obj.fire_crew or not obj.fire_crew.name:
            return "-"
        return obj.fire_crew.name

    def employees_parameters_block_for_admin(self, obj, request):
        FIELDS = [
            "surname",
            "given_name",
            "middle_name",
            "job_title",
            "Crew",
            "Email",
            "MobilePhone",
            "Ranking 1 to 10",
            "Rating",
            "Ready",
            "Available for Dispatch",
            "Currency Exp. Date",
            "Current Refresher Date",
            "Current Pack Test Date",
            "Current trainee",
            "Dispatch Category",
            "Dispatch Center",
            "DOB",
            "E-Verify",
            "EMT",
            "End of Season Call",
            "EXPERIENCE AND LSA",
            "Eye Color",
            "Female (Company Manifest)",
            "Field Training",
            "Field Training Completion Date",
            "File Updated Through",
            # "file_as",
            # "Finger Print Experation",
            "First Aid (Instructor)",
            "First Aid Online",
            "First Aid Skills Session",
            "First Aid/CPR",
            "ICA Number",
            "ICS Certification Date",
            "Identification Type",
            "Instructor 1",
            "Last Fire",
            "Last day on fire",
            "Last Login LD",
            "Male (For Company Manifest)",
            "MSPA Conviction Question 1",
            "MSPA Conviction Question 2",
            "Payroll ID",
            "Race/Ethnicity",
            "Rec(fd) CRWB Fire Days",
            "Rec(fd) CRWB Hotline Fires",
            "Rec(fd) CRWB(T) Fire Days",
            "Rec(fd) CRWB(T) Hotline Fires",
            "Rec(fd) ENGB Fire Days",
            "Rec(fd) ENGB Hotline Fires",
            "Rec(fd) ENGB(T) Fire Days",
            "Rec(fd) ENGB(T) Hotline Fires",
            "Rec(fd) F1 Fire Days",
            "Rec(fd) F1 Hotline Fires",
            "Rec(fd) F1(T) Fire Days",
            "Rec(fd) F1(T) Hotline Fires",
            "Rec(fd) F2 Fire Days",
            "Rec(fd) F2 Hotline Fires",
            "Rec(fd) 2023 Fire Days",
            "Rec(fd) 2024 Fire Days",
            "Rec(fd) 2025 Fire Days",
            "Rec(fd) 2026 Fire Days",
            # "Records CRWB(T) Fire Days",
            # "Records CRWB(T) Hotline Fires",
            # "Records F1 Fire Days",
            # "Records F1 Hotline Fires",
            # "Records F1(T) Fire Days",
            # "Records F1(T) Hotline Fires",
            # "Records F2 Fire Days",
            # "Records F2 Hotline Fires",
            "Sawyer",
            "Unvailable Date",
            "WFTG Profile",
            "Not Eligible to Work (Button)",
            "Employee Working Status",
        ]

        employee = Employees.objects.prefetch_related(
            Prefetch(
                "employees_parameters_entries",
                queryset=Employees_Parameters.objects.select_related("contacts_prop"),
                to_attr="parameters",
            )
        ).get(id=obj.id)

        order_case = Case(
            *[When(property_name=name, then=idx) for idx, name in enumerate(FIELDS)],
            output_field=IntegerField(),
        )

        all_params = list(
            Contacts_Prop.objects.filter(property_name__in=FIELDS)
            .annotate(_ord=order_case)
            .order_by("_ord")
            # .order_by("property_name")
            .values_list("id", "property_name", "property_type")
        )

        data = get_employee_params_dict(employee, all_params)

        html_content = render_to_string(
            "admin/employees/employees_parameters_block.html",
            {
                "employee_id": employee.id,
                "employee_email": employee.get_email,
                "data": data,
            },
            request=request,
        )

        return mark_safe(html_content)

    def employees_parameters_custom_block_for_admin(self, obj, request):
        FIELDS = {
            "Availability": [
                None,  # Empty field for table column alignment (updated_at)
                "Availability status",
                # "Date of change",
                "Date of expected future change",
                "Current State Dispatching From",
                "Current City Dispatching From",
                "Travel Time",
                "Availability notes",
            ],
            "Dispatching statuses": [
                None,  # Empty field for table column alignment (updated_at)
                # "Dispatch Status Update Date",
                # "Dispatch Status Update Time",
                "Dispatch Call Status",
                "Dispatch Category",
                "ETA, Late, Dispatch",
                "Dispatch location",
                "Dispatch notes",
            ],
            "Interactions": [
                None,  # Empty field for table column alignment (updated_at)
                "Type of interaction",
                "Last Attempted Communication",
                "Negative interaction",
                "Interaction notes",
            ],
            "Driver's License": [
                "Driver's License Issue Date",
                "Driver's License Expiration Date",
                "Driver's License State, Number",
                "Driver's License Endorsements",
                "Driver's License Restrictions",
                # "Driver's License Document",
                "Front of ID",
                "Back of ID",
                "ID 2 Front",
                "ID 2 Back",
            ],
            "Passport": [
                "Passport Issue Date",
                "Passport Expiration Date",
                "Passport Number",
                "Passport Document",
            ],
            "Social Security Number": [
                "Social Security Issue Date",
                "Social Security Expiration Date",
                "Social Security Number",
                "Social Security Document",
            ],
            "Drug test": [
                "Drug Test date",
                "Drug Test preseason",
            ],
            "Employment Packet": [
                "Employee Packet",
                "Current Pack Test Date",
                "Current Pack Test Date signed",
                "Pack Test document",
            ],
            "IQC Card": [
                "IQC Position",
                "Packtest Results",
                "IQC Issue date",
                "IQC document",
            ],
            "Manifest": [
                # "Manifest Date, 2025",
                # "Manifest Date, 2024",
                # "Manifest Date, 2023",
                # "Manifest Date, 2022",
                # "Manifest Date, 2021",
                "Manifest Date",
            ],
            "MSPA": [
                "MSPA Issue date",
                "MSPA Expiration Date",
                "MSPA Number",
                "MSPA Pending",
                "MSPA document",
            ],
            "Medical Card": [
                "Medical Card Issue Date",
                "Medical Card Expiration Date",
                "Medical Card Type",
                "Medical Card Document",
            ],
            "Fingerprint": [
                "FP Issue date",
                "FP Expiration Date",
                "FP document",
            ],
        }

        availability_table = render_table(
            obj,
            Availability,
            columns=[
                "updated_at",
                "availability_status",
                # "date_of_change",
                "date_of_expected_future_change",
                "location_state",
                "location_city",
                "travel_time",
                "notes",
            ],
        )
        dispatchingstatus_table = render_table(
            obj,
            DispatchingStatus,
            columns=[
                "updated_at",
                # "date",
                # "time",
                "dispatch_status",
                "dispatch_category",
                "ETA",
                "location",
                "notes",
            ],
        )
        interaction_table = render_table(
            obj,
            Interaction,
            columns=[
                "updated_at",
                "type_of_interaction",
                "date",
                "negative_interaction",
                "notes",
            ],
        )

        html_blocks = {
            "Availability": mark_safe(
                availability_table
                + format_html(
                    # Add rel="noreferrer noopener" for security, and break long line for linting
                    (
                        '<br><a style="margin: 5px 5px 0 10px;" target="_blank" '
                        'rel="noreferrer noopener" '
                        'href="/admin/company/availability/?q={}">History</a>'
                    ),
                    obj.get_email,
                )
            ),
            "Dispatching statuses": mark_safe(
                dispatchingstatus_table
                + format_html(
                    # Add rel="noreferrer noopener" for security
                    (
                        '<br><a style="margin: 5px 5px 0 10px;" target="_blank" '
                        'rel="noreferrer noopener" '
                        'href="/admin/company/dispatchingstatus/?q={}">History</a>'
                    ),
                    obj.get_email,
                )
            ),
            "Interactions": mark_safe(
                interaction_table
                + format_html(
                    '<br><a style="margin: 5px 5px 0 10px;" target="_blank" '
                    'rel="noreferrer noopener" '
                    'href="/admin/company/interaction/?q={}">History</a>',
                    obj.get_email,
                )
            ),
            "Driver's License": format_html(
                '<a style="margin: 5px 5px 0 10px;" target="_blank" '
                'rel="noreferrer noopener" '
                'href="/admin/company/driverlicense/?q={}">History</a>',
                obj.get_email,
            ),
            "Passport": format_html(
                '<a style="margin: 5px 5px 0 10px;" target="_blank" '
                'rel="noreferrer noopener" '
                'href="/admin/company/passport/?q={}">History</a>',
                obj.get_email,
            ),
            "Social Security Number": format_html(
                '<a style="margin: 5px 5px 0 10px;" target="_blank" '
                'rel="noreferrer noopener" '
                'href="/admin/company/socialsecuritynumber/?q={}">History</a>',
                obj.get_email,
            ),
            "Medical Card": format_html(
                '<a style="margin: 5px 5px 0 10px;" target="_blank" '
                'rel="noreferrer noopener" '
                'href="/admin/company/medicalcard/?q={}">History</a>',
                obj.get_email,
            ),
            "Drug test": format_html(
                '<a style="margin: 5px 5px 0 10px;" target="_blank" '
                'rel="noreferrer noopener" '
                'href="/admin/company/drugtest/?q={}">History</a>',
                obj.get_email,
            ),
            "Employment Packet": format_html(
                '<a style="margin: 5px 5px 0 10px;" target="_blank" '
                'rel="noreferrer noopener" '
                'href="/admin/company/employmentpacket/?q={}">History</a>',
                obj.get_email,
            ),
            "IQC Card": format_html(
                '<a style="margin: 5px 5px 0 10px;" target="_blank" '
                'rel="noreferrer noopener" '
                'href="/admin/company/iqccard/?q={}">History</a>'
                '<a style="margin: 5px 5px 0 10px; cursor: pointer;" '
                'onclick="window.open(\'{}\', \'pdfDownload\', '
                '\'width=500,height=600,left=\' + (screen.width - 100) + \',top=\' + (screen.height - 100) + '
                '\',resizable=no,scrollbars=no,menubar=no,toolbar=no,status=no\'); return false;">RedCard_(pdf)</a>',
                obj.get_email,
                reverse("cards_create") + "?" + urlencode({"id": obj.id, "pdf": "True"}),
            ),
            "Manifest": format_html(
                '<a style="margin: 5px 5px 0 10px;" target="_blank" '
                'rel="noreferrer noopener" '
                'href="/admin/company/companymanifest/?q={}">History</a>',
                obj.get_email,
            ),
            "MSPA": format_html(
                '<a style="margin: 5px 5px 0 10px;" target="_blank" '
                'rel="noreferrer noopener" '
                'href="/admin/company/mspa/?q={}">History</a>',
                obj.get_email,
            ),
        }

        grouped_params = get_grouped_parameters(
            obj, FIELDS, extra_html_blocks=html_blocks
        )

        html_content = render_to_string(
            "admin/edit_inline/custom_inline_params.html",
            {
                "grouped_params": grouped_params,
                "html_blocks": html_blocks,
                "employee_id": obj.id,
            },
            request=request,
        )

        return mark_safe(html_content)

    def employees_parameters_custom_block_for_admin_light(self, obj, request):
        FIELDS = {
            "additional": [
                (
                    "I-9 file",
                    "I9",
                ),
                (
                    "E-Verify file",
                    "E-Verify",
                ),
                "Dispatch Call Status",
            ],
        }

        html_blocks = {}

        grouped_params = get_grouped_parameters(
            obj, FIELDS, extra_html_blocks=html_blocks
        )

        html_content = render_to_string(
            "admin/edit_inline/custom_inline_params_light.html",
            {
                "grouped_params": grouped_params,
                "html_blocks": html_blocks,
            },
            request=request,
        )

        return mark_safe(html_content)

    # @admin.display(description="")
    # def employees_info_block_for_admin(self, obj):
    #     html_content = render_to_string(
    #         "admin/employees/employees_info_block.html",
    #         {
    #             "employee": obj,
    #         }
    #     )
    #     return mark_safe(html_content)

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (
                None,
                {
                    "fields": (
                        "show_emp_info",
                        (
                            "document_preview",
                            "fire_crew",
                            "type",
                            "is_manifested",
                        ),
                        # (
                        # "document_preview",
                        # "employees_info_block_for_admin"
                        # ),
                        "document",
                        "user",
                        # "created_at",
                        "last_modified_name",
                        # "tags",
                        "updated_at",
                        # "last_modified_time",
                        # "datetime_created",
                        (
                            (
                                # "pull_link_exc",
                                "refresh_link_privser",
                                "force_push_link_exc",
                                "force_push_link_privser",
                                "remove_link",
                            )
                            if request.user.username in SPECIAL_USERS_SET
                            else ()
                        ),
                    ),
                },
            ),
        ]

        if obj:
            fieldsets.append(
                (
                    None,
                    {
                        "fields": (),
                        "description": self.employees_parameters_custom_block_for_admin_light(
                            obj, request
                        ),
                    },
                )
            )
            fieldsets.append(
                (
                    None,
                    {
                        "fields": (),
                        "description": self.employees_parameters_block_for_admin(
                            obj, request
                        ),
                    },
                )
            )
            # fieldsets.append((
            #     None, {
            #     "fields": ("tags",),
            # }
            # ))
            fieldsets.append(
                (
                    None,
                    {
                        "fields": (),
                        "description": self.employees_parameters_custom_block_for_admin(
                            obj, request
                        ),
                    },
                )
            )
            fieldsets.append(
                (
                    None,
                    {
                        "fields": (),
                        "description": self.paychecks_block_for_admin(obj, request),
                    },
                )
            )
        return fieldsets

    readonly_fields = [
        "show_emp_info",
        # "email",
        "document_preview",
        # "pull_link_exc",
        # "force_push_link_exc",
        # "force_push_link_privser",
        # "employees_info_block_for_admin",
        "contact_id",
        "last_modified_name",
        "last_modified_time",
        "datetime_created",
        "created_at",
        "updated_at",
        "is_manifested",
    ]

    def get_readonly_fields(self, request, obj=None):
        fields = [
            "show_emp_info",
            # "email",
            "document_preview",
            # "pull_link_exc",
            # "force_push_link_exc",
            # "force_push_link_privser",
            # "employees_info_block_for_admin",
            "contact_id",
            "last_modified_name",
            "last_modified_time",
            "datetime_created",
            "created_at",
            "updated_at",
            "is_manifested",
        ]
        if request.user.username in SPECIAL_USERS_SET:
            # fields.append("pull_link_exc")
            fields.append("refresh_link_privser")
            fields.append("force_push_link_exc")
            fields.append("force_push_link_privser")
            fields.append("remove_link")
        return fields

    # list_filter = ("status_code", "email")
    list_filter = (EmployeesStateFilter, "tags")

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        employee_instance = form.instance

        # --- files ---
        for key, file in request.FILES.items():
            try:
                param_id = int(key)
            except ValueError:
                continue  # skip non-numeric keys

            # safety: accept files только для Document-свойств
            try:
                prop_type = (
                    Contacts_Prop.objects.only("property_type")
                    .get(id=param_id)
                    .property_type
                )
            except Contacts_Prop.DoesNotExist:
                continue
            if prop_type != Contacts_Prop.TypeChoices.DOCUMENT:
                continue

            param, created = Employees_Parameters.objects.get_or_create(
                employee=employee_instance,
                contacts_prop_id=param_id,
                defaults={"value_file": file, "value": ""},
            )
            if not created:
                # delete old blob if present before overwrite
                if param.value_file:
                    try:
                        param.value_file.delete(save=False)
                    except Exception:
                        pass
                param.value_file = file
                param.value = ""
                param.save(update_fields=["value_file", "value"])

        # --- deletions ---
        for key in request.POST.keys():
            if not key.startswith("delete_"):
                continue
            try:
                param_id = int(key.replace("delete_", ""))
            except ValueError:
                continue

            param = Employees_Parameters.objects.filter(
                employee=employee_instance, contacts_prop_id=param_id
            ).first()
            if param and param.value_file:
                try:
                    param.value_file.delete(save=False)
                except Exception:
                    pass
                param.value_file = None
                param.save(update_fields=["value_file"])

        # trigger entities generation
        from core.tasks import generate_entities_from_contact_params_task

        if settings.DEBUG:
            generate_entities_from_contact_params_task.run(
                employee_id=employee_instance.id
            )
        else:
            generate_entities_from_contact_params_task.delay(
                employee_id=employee_instance.id
            )

        transaction.on_commit(
            lambda: EmployeesService.update_employee_tags(
                employee=employee_instance, modified_name=""
            )
        )

    class Media:
        css = {
            "all": (
                "core/custom_styles.css",
                # "grappelli/css/admin_breadcrumbs.css",
                # "core/custom_inline.css",
                "admin/css/employee_params_form.css",
                "admin/css/hide_default_add.css",
                "admin/css/emp_info.css",
                "admin/css/modal.css",
            )
        }
        js = (
            # "grappelli/js/admin_breadcrumbs.js",
            "admin/js/employee_params_form.js",
            "admin/js/employee_photo.js",
            # "admin/js/custom_fire_run_button.js",
            "admin/js/custom_inlines_button.js",
            "admin/js/employee_modal_forms.js",
        )


def render_table(employee, instance_obj, columns):
    # columns = [
    #     "availability_status",
    #     "date_of_change",
    #     "date_of_expected_future_change",
    #     "location_state",
    #     "location_city",
    #     "travel_time",
    #     "notes",
    # ]

    def format_value(val, col_name):
        if isinstance(val, date):
            if col_name == "updated_at":
                return val.astimezone().strftime("%m/%d/%Y %H:%M")
            return val.strftime("%m/%d/%Y")
        if val is None:
            return ""
        return str(val)

    # Get records with IDs for data attributes
    records = (
        instance_obj.objects.filter(employee=employee)
        .order_by("-updated_at")[:10]
    )

    rows_data = []
    for record in records:
        row_values = []
        for col in columns:
            val = getattr(record, col, None)
            row_values.append((format_value(val, col), col))
        rows_data.append((record.id, row_values))

    header = ""
    # header = format_html(
    #     "<tr>{}</tr>",
    #     format_html_join(
    #         "",
    #         "<th style='min-width: 260px'>{}</th>",
    #         ((col.replace("_", " ").title(),) for col in columns)
    #     )
    # )

    body = format_html_join(
        "",
        '<tr data-record-id="{}">{}</tr>',
        (
            (
                record_id,
                format_html_join(
                    "",
                    "<td style='min-width: 260px'>{}</td>",
                    ((val,) for val, col_name in row_values),
                ),
            )
            for record_id, row_values in rows_data
        ),
    )

    # if not rows_data:
    #     return format_html("<p>No availability records found.</p>")

    return format_html(
        '<table style="width: auto" class="grp-table table-history">{}</table>',
        format_html("{}{}", header, body),
    )
