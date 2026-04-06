from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import Fire, Crew
from pdf_plugin.admin_mixin import PDFGenerateMixin


class CrewInline(admin.TabularInline):
    model = Crew
    autocomplete_fields = ("fire",)
    fields = (
        "crew_name",
        # "crew_boss",
        # "fire",
        "c_number",
        "contract",
    )
    readonly_fields = ()
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("-id",)


@admin.register(Fire)
class FireAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 250
    search_fields = ("fire_number", "incident_name", "agency", "state")
    list_display = (
        # "updated_at",
        "fire_number",
        "incident_name",
        "incident_type",
        # "reliability_leaving",
        "agency",
        "state",
        "activity_code",
        "fuel_type",
        "fire_size",
        # "modified_by",
    )
    list_editable = (
        # "fire_number",
        "incident_name",
        "incident_type",
        # "reliability_leaving",
        "agency",
        "state",
        "activity_code",
        "fuel_type",
        "fire_size",
    )
    ordering = ()

    fields = (
        "fire_number",
        "incident_name",
        "incident_type",
        # "reliability_leaving",
        "agency",
        "state",
        "activity_code",
        "fuel_type",
        "fire_size",
        ("updated_at", "modified_by"),
    )
    readonly_fields = (
        "updated_at",
        "modified_by",
    )

    list_filter = ("updated_at", "state", "agency")

    inlines = (CrewInline,)
