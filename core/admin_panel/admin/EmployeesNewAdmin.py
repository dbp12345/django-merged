from django.contrib import admin
from django.db.models import Count, Prefetch
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse

# from company.models.EmployeesParameters import Employees_Parameters
from django.utils.safestring import mark_safe
from django_admin_flexlist import FlexListAdmin

from company.models import Employees_Parameters, Employees_Pictures
from company.models.Employees import *

from exchange.models import Contacts_Prop


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
        ("photo_privser_picture_at_field_training_preview", "photo_privser_picture_at_field_training"),
        ("photo_privser_cropped_picture_for_red_card_preview", "photo_privser_cropped_picture_for_red_card"),
        # ("photo_privser_passport_picture_preview", "photo_privser_passport_picture"),
        # "edit_link",
    )
    readonly_fields = (
        "photo_privser_picture_at_field_training_preview",
        "photo_privser_cropped_picture_for_red_card_preview",
        # "photo_privser_passport_picture_preview",
        # "edit_link",
    )
    extra = 0
    can_delete = True
    # ordering = ()


class EmergencyContactInline(admin.TabularInline):
    # def has_add_permission(self, request, obj=None):
    #     return False

    model = EmergencyContact
    fk_name = "employee"
    fields = (
        "type",
        "relation_to_you",
        "is_primary",
        "relationship",
        # "edit_link",
    )
    readonly_fields = (
        "relationship",
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class MSPAInline(admin.TabularInline):
    # def has_add_permission(self, request, obj=None):
    #     return False

    model = MSPA
    fields = (
        "issue_date",
        "expiration_date",
        "MSPA_number",
        # "document",
        "document_preview",
        # "edit_link",
    )
    readonly_fields = (
        "document_preview",
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class IdentificationDocumentsInline(admin.TabularInline):
    # def has_add_permission(self, request, obj=None):
    #     return False

    model = IdentificationDocuments
    fields = (
        "type",
        "issue_date",
        "expiration_date",
        "number",
        "endorsement",
        "restriction",
        # "document",
        "document_preview",
        "updated_at",
        # "edit_link",
    )
    readonly_fields = (
        "document_preview",
        "updated_at",
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)


class DispatchingStatusInline(admin.TabularInline):
    # def has_add_permission(self, request, obj=None):
    #     return False

    model = DispatchingStatus
    fields = (
        "date",
        "positive_interaction",
        "dispatch_status",
        "dispatch_category",
        "ETA",
        "location",
        "notes",
        # "edit_link",
    )
    readonly_fields = (
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class CompanyManifestInline(admin.TabularInline):
    model = CompanyManifest
    fields = (
        "date",
        # "edit_link",
    )
    readonly_fields = (
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class DrugTestInline(admin.TabularInline):
    model = DrugTest
    fields = (
        "date",
        "result",
        # "edit_link",
    )
    readonly_fields = (
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class NomexCheckOutInline(admin.TabularInline):
    model = NomexCheckOut
    fields = (
        "date",
        "pants_serial_number",
        "shirt_serial_number",
        # "edit_link",
    )
    readonly_fields = (
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class NomexCheckInInline(admin.TabularInline):
    model = NomexCheckIn
    fields = (
        "date",
        "pants_serial_number",
        "shirt_serial_number",
        # "edit_link",
    )
    readonly_fields = (
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class EmploymentPacketInline(admin.TabularInline):
    model = EmploymentPacket
    fields = (
        "packet_name",
        "date_sent",
        "date_signed",
        # "document",
        "document_preview",
        # "edit_link",
    )
    readonly_fields = (
        "document_preview",
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class IQCCardInline(admin.TabularInline):
    model = IQCCard
    fields = (
        "position",
        "pack_test",
        "document",
        "date",
        # "edit_link",
    )
    readonly_fields = (
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class InteractionInline(admin.TabularInline):
    model = Interaction
    fields = (
        "type_of_interaction",
        "date",
        "negative_interaction",
        "notes",
        # "edit_link",
    )
    readonly_fields = (
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class TaskBookInline(admin.TabularInline):
    model = TaskBook
    fields = (
        "type_of_taskbook",
        "initiated_date",
        "completed_date",
        "updated_date",
        "final_evaluator",
        "document_preview",
        "document",
        # "edit_link",
    )
    readonly_fields = (
        "document_preview",
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class NotesInline(admin.TabularInline):
    model = Notes
    fields = (
        "body",
        # "edit_link",
    )
    readonly_fields = (
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class AvailabilityInline(admin.TabularInline):
    model = Availability
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)
    readonly_fields = (
        # "edit_link",
    )

    fields = (
        "availability_status",
        # "date_of_change",
        "date_of_expected_future_change",
        "location_state",
        "location_city",
        "travel_time",
        "notes",
        # "edit_link",
    )

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class CurrentAssignedInline(admin.TabularInline):
    model = CurrentAssigned
    fields = (
        "date",
        # "edit_link",
    )
    readonly_fields = (
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class CourseInline(admin.TabularInline):
    model = Course
    fields = (
        "training_type",
        "inperson_required",
        "governing_body",
        # "edit_link",
    )
    readonly_fields = (
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class TrainingClassInline(admin.TabularInline):
    model = TrainingClass
    # fk_name = "employee"
    fields = (
        "instructor",
        "course",
        "test_score",
        "date",
        "location",
        # "document",
        "document_preview",
        # "edit_link",
    )
    readonly_fields = (
        "document_preview",
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class StudentInline(admin.TabularInline):
    model = Student
    autocomplete_fields = ("training_class",)
    fields = (
        # "get_training_type_name",
        "training_class",
        "test_score",
        "document_preview",
        "document",
        # "edit_link",
    )
    readonly_fields = (
        # "get_training_type_name",
        # "training_class",
        "document_preview",
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("training_class__course__training_type__name", "-training_class__date")

    @admin.display(description="Course")
    def get_training_type_name(self, instance):
        url = reverse("admin:%s_%s_change" % (Course._meta.app_label, Course._meta.model_name), args=[instance.training_class.course.pk])
        return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, instance.training_class.course.training_type.name)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class RateOfPayInline(admin.TabularInline):
    model = RateOfPay
    fields = (
        "base_rate",
        "bonus_rate",
        "office_rate",
        "year",
        "date",
        # "edit_link",
    )
    readonly_fields = (
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class FireInline(admin.TabularInline):
    model = Fire
    fields = (
        "fire_number",
        "incident_name",
        "incident_type",
        # "reliability_leaving",
        "agency",
        "state",
        # "edit_link",
    )
    readonly_fields = (
        # "edit_link",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class FireRunInline(admin.TabularInline):
    model = FireRun

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # autocomplete_fields = ("crew", )

    # def crew_display(self, instance):
    #     if instance.crew:
    #         return format_html(
    #             "<span style='white-space: nowrap !important;'>{}</span>",
    #             str(instance.crew)
    #         )
    #     return "-"
    #
    # crew_display.short_description = "Crew"

    @admin.display(description="Crew boss")
    def crew_crew_name(self, instance):
        if instance.crew:
            return instance.crew.crew_name
        return "-"

    @admin.display(description="Agency")
    def crew_fire_agency(self, instance):
        if instance.crew and instance.crew.fire:
            return instance.crew.fire.agency
        return "-"

    @admin.display(description="State")
    def crew_fire_state(self, instance):
        if instance.crew and instance.crew.fire:
            return instance.crew.fire.state
        return "-"

    @admin.display(description="Fire Number")
    def crew_fire_fire_number(self, instance):
        if instance.crew and instance.crew.fire:
            return instance.crew.fire.fire_number
        return "-"

    @admin.display(description="Management Type or Complexity Level")
    def crew_fire_incident_type(self, instance):
        if instance.crew and instance.crew.fire:
            return instance.crew.fire.incident_type
        return "-"

    @admin.display(description="Incident Name")
    def crew_fire_incident_name(self, instance):
        if instance.crew and instance.crew.fire:
            return instance.crew.fire.incident_name
        return "-"

    fields = (
        "job_title",
        "activity_code",
        "start_date",
        "crew_fire_agency",
        "crew_fire_state",
        "operational_periods",
        "crew_fire_incident_type",
        "fuel_type",
        "fire_size",
        "crew_fire_incident_name",
        "crew_crew_name",
        "hotline_shifts",
        "eval_hotline",
        "hotline_in_remarks",
        "rating",
        "ranking",

        # "crew_fire_fire_number",

        # "crew_display",
        # # "crew",
        # "CRWB_potential",
        # "rating",
        # "ranking",
        # "professionalism_rating",
        # "attitude_rating",
        # "sawyer_rating",
        # "month_year",
        # "hotline_shifts",
    )
    readonly_fields = (
        "job_title",
        "activity_code",
        "start_date",
        "crew_fire_agency",
        "crew_fire_state",
        "operational_periods",
        "crew_fire_incident_type",
        "fuel_type",
        "fire_size",
        "crew_fire_incident_name",
        "crew_crew_name",
        "hotline_shifts",
        "eval_hotline",
        "hotline_in_remarks",
        "rating",
        "ranking",

        # "crew_fire_fire_number",

        # "crew_display",
        # # "crew",
        # "CRWB_potential",
        # "rating",
        # "ranking",
        # "professionalism_rating",
        # "attitude_rating",
        # "sawyer_rating",
        # "month_year",
        # "hotline_shifts",
    )
    extra = 0
    can_delete = False
    can_add = False
    show_change_link = False
    ordering = ("job_title",)

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class DrawsInline(admin.TabularInline):
    model = Draws
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-updated_at",)
    readonly_fields = (
        # "edit_link",
    )

    fields = (
        "date",
        "type",
        "amount",
        "signature",
        "payer",
        # "edit_link",
    )

    # def edit_link(self, instance):
    #     if instance.pk:
    #         url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name), args=[instance.pk])
    #         return format_html('<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>', url, "edit")
    #     return "-"
    #
    # edit_link.short_description = ""


class EmployeesStateFilter(admin.SimpleListFilter):
    title = "Type"
    parameter_name = "type"

    def lookups(self, request, model_admin):
        types = Employees.objects.values("type").annotate(count=Count("type"))
        return [(employee_type["type"], f"{employee_type['type']} ({employee_type['count']})") for employee_type in types]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(type=self.value())
        return queryset


def crew_list_display(obj):
    if not obj.fire_crew:
        return "No crew assigned"
    return f"<b>{obj.fire_crew.name}</b>"


def get_employee_params_dict(employee, params):
    param_dict = {p.contacts_prop.id: p.value for p in getattr(employee, "parameters", [])}
    return {param: param_dict.get(param[0], "") for param in params}


@admin.register(ContactsExchange)
class EmployeesNewAdmin(FlexListAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_model_perms(self, request):
        return {}

    def changelist_view(self, request, extra_context=None):
        return redirect(reverse("employees_table"))

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            "emergency_contact_entries",
            "mspa_entries",
            "identification_documents_entries",
            "dispatching_status_entries",
            "company_manifest_entries",
            "drug_test_entries",
            "nomex_checkout_entries",
            "nomex_checkin_entries",
            "employment_packet_entries",
            "IQC_card_entries",
            "interaction_entries",
            "task_book_entries",
            "availability_entries",
            "current_assigned_entries",
            "training_class_entries_as_instructor",
            "student_entries",
            "rate_of_pay_entries",
            "fire_run_entries",
            "draws_entries",
        )

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        if obj:
            full_name = " ".join(filter(None, [obj.name]))
            full_info = ", ".join(filter(None, [full_name, obj.get_email, obj.get_job_title]))
            self.model._meta.verbose_name = full_info
        return obj

    inlines = (
        # EmployeesParametersInline,
        AvailabilityInline,
        TrainingClassInline,
        CurrentAssignedInline,
        DispatchingStatusInline,
        DrugTestInline,
        EmergencyContactInline,
        EmploymentPacketInline,
        IdentificationDocumentsInline,
        InteractionInline,
        IQCCardInline,
        CompanyManifestInline,
        MSPAInline,
        NomexCheckInInline,
        NomexCheckOutInline,
        RateOfPayInline,
        StudentInline,
        TaskBookInline,
        DrawsInline,
        NotesInline,
        EmployeesPicturesInline,
        FireRunInline,
    )

    list_per_page = 100
    search_fields = ("email", "id")

    @admin.display(description="")
    def pull_link_exc(self, obj):
        url = reverse("update_contact_from_exchange_by_email", kwargs={"obj_id": obj.id})
        return format_html(
            '<a class="button" style="background: var(--button-bg);" href="{}">PULL from Exchange</a>',
            url
        )

    @admin.display(description="")
    def force_push_link_exc(self, obj):
        url = reverse("contact_forcepush_to_exchange", kwargs={"obj_id": obj.id})
        return format_html(
            '<a class="button" style="background: var(--button-bg);" href="{}">Force PUSH to Exchange</a>',
            url
        )

    @admin.display(description="")
    def force_push_link_privser(self, obj):
        url = reverse("contact_forcepush_to_privser", kwargs={"obj_id": obj.id})
        return format_html(
            '<a class="button" style="background: var(--button-bg);" href="{}">Force PUSH to Privser</a>',
            url
        )

    @admin.display(description="Email")
    def short_email(self, obj):
        if len(obj.email) > 36:
            return f"{obj.email[:36]}..."
        return obj.email

    list_display = (
        "short_email",
        "phone",
        "type",
        "first_name",
        "middle_name",
        "last_name",
        "job_title",
        "crew_list",
        "last_modified_name",
        "last_modified_time",
        "updated_at",
        # "pull_link_exc",
        # "force_push_link_exc",
        # "force_push_link_privser",
    )

    def get_list_display(self, request):
        fields = [
            "short_email",
            "phone",
            "type",
            "first_name",
            "middle_name",
            "last_name",
            "job_title",
            "crew_list",
            "last_modified_name",
            "last_modified_time",
            "updated_at",
            # "pull_link_exc",
            # "force_push_link_exc",
            # "force_push_link_privser",
        ]
        if request.user.username in ["admin", "dima", "csnortland", "operations"]:
            fields.append("pull_link_exc")
            fields.append("force_push_link_exc")
            fields.append("force_push_link_privser")
        return fields

    list_editable = (
        "type",
        "first_name",
        "middle_name",
        "last_name",
        "job_title",
    )
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
        employee = Employees.objects.prefetch_related(
            Prefetch(
                "employees_parameters_entries",
                queryset=Employees_Parameters.objects.select_related("contacts_prop"),
                to_attr="parameters"
            )
        ).get(id=obj.id)

        all_params = list(
            Contacts_Prop.objects.filter(visibility=True, param_mirror=False)
            .values_list("id", "property_name", "property_type").order_by("property_name")
        )

        data = get_employee_params_dict(employee, all_params)

        html_content = render_to_string(
            "admin/employees/employees_parameters_block.html",
            {
                "employee_id": employee.id,
                "data": data,
            },
            request=request
        )

        return mark_safe(html_content)

    @admin.display(description="")
    def employees_info_block_for_admin(self, obj):
        html_content = render_to_string(
            "admin/employees/employees_info_block.html",
            {
                "employee": obj,
            }
        )
        return mark_safe(html_content)

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (None, {
                "fields": (
                    ("fire_crew", "type") + (("pull_link_exc", "force_push_link_exc", "force_push_link_privser") if request.user.username in ["admin", "dima", "csnortland", "operations"] else ()),
                    ("document_preview", "employees_info_block_for_admin"),
                    "document",
                    (
                        # "created_at",
                        "updated_at",
                        "last_modified_name",
                        "last_modified_time",
                        "datetime_created",
                    ),
                ),
            }),
        ]

        if obj:
            fieldsets.append((
                None, {
                "fields": (),
                "description": self.employees_parameters_block_for_admin(obj, request)
            }
            ))
        return fieldsets

    readonly_fields = [
        # "email",
        "document_preview",
        # "pull_link_exc",
        # "force_push_link_exc",
        # "force_push_link_privser",
        "employees_info_block_for_admin",
        "contact_id",
        "last_modified_name",
        "last_modified_time",
        "datetime_created",
        "created_at",
        "updated_at",
    ]

    def get_readonly_fields(self, request, obj=None):
        fields = [
            # "email",
            "document_preview",
            # "pull_link_exc",
            # "force_push_link_exc",
            # "force_push_link_privser",
            "employees_info_block_for_admin",
            "contact_id",
            "last_modified_name",
            "last_modified_time",
            "datetime_created",
            "created_at",
            "updated_at",
        ]
        if request.user.username in ["admin", "dima", "csnortland", "operations"]:
            fields.append("pull_link_exc")
            fields.append("force_push_link_exc")
            fields.append("force_push_link_privser")
        return fields

    # list_filter = ("status_code", "email")
    list_filter = (EmployeesStateFilter,)

    class Media:
        css = {
            "all": (
                "core/custom_styles.css",
                # "grappelli/css/admin_breadcrumbs.css",
                # "core/custom_inline.css",
                "admin/css/employee_params_form.css",
                "admin/css/hide_default_add.css",
            )
        }
        js = (
            # "grappelli/js/admin_breadcrumbs.js",
            # "admin/js/employee_params_form.js",
            "admin/js/employee_photo.js",
            # "admin/js/custom_fire_run_button.js",
            "admin/js/custom_inlines_button.js",
        )
