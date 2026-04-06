from django.contrib import admin
from django_admin_flexlist import FlexListAdmin

from company.models.Employees import Course, TrainingClass
from pdf_plugin.admin_mixin import PDFGenerateMixin


class TrainingClassInline(admin.TabularInline):
    show_change_link = False
    model = TrainingClass

    # def edit_link(self, instance):
    #     url = reverse("admin:%s_%s_change" % (instance._meta.app_label,
    # instance._meta.model_name),
    # args=[instance.id]
    # )
    #     return format_html(
    # '<a href="{}" target="_blank" rel="noreferrer noopener">{}</a>',
    # url,
    # instance.date.strftime("%m/%d/%Y")
    # )
    #
    # edit_link.short_description = "class"

    fields = (
        # "updated_at_link",
        "date",
        # "edit_link",
        "instructor",
        "course",
        "test_score",
        "location",
        "students_count",
        # "modified_by",
    )
    readonly_fields = (
        "date",
        # "edit_link",
        "instructor",
        # "updated_at_link",
        "modified_by",
        "students_count",
    )
    extra = 0
    can_delete = True
    show_change_link = True
    ordering = ("date",)

    # def updated_at_link(self, instance):
    #     url = reverse("admin:%s_%s_change" % (instance._meta.app_label,
    # instance._meta.model_name),
    # args=[instance.id])
    #     return format_html('<a href="{}">{}</a>', url, instance.updated_at.strftime('%m/%d/%Y %H:%M'))
    #
    # updated_at_link.short_description = "Updated At"

    @admin.display(description="Students Count")
    def students_count(self, obj):
        return obj.student_entries.count()


@admin.register(Course)
class CourseAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False

    list_per_page = 50
    search_fields = ("governing_body",)
    list_display = (
        # "name",
        "training_type",
        "inperson_required",
        "governing_body",
        "classes_count",
        # "updated_at",
        # "modified_by",
    )
    list_editable = (
        # "name",
        # "training_type",
        "inperson_required",
        "governing_body",
    )
    fields = (
        # "name",
        "training_type",
        "inperson_required",
        "governing_body",
        "updated_at",
        "modified_by",
        "classes_count",
    )
    readonly_fields = (
        "updated_at",
        "modified_by",
        "classes_count",
    )

    list_filter = ("training_type", "inperson_required")

    inlines = (
        TrainingClassInline,
    )

    @admin.display(description="Classes Count")
    def classes_count(self, obj):
        return obj.training_class_entries.count()
