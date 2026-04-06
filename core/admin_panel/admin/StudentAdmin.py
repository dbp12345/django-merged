from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import Student
from pdf_plugin.admin_mixin import PDFGenerateMixin


@admin.register(Student)
class StudentAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False
    list_per_page = 50
    search_fields = ("employee__email",)
    autocomplete_fields = ("employee", "training_class",)
    list_display = (
        "updated_at",
        "employee",
        "get_course",
        "training_class",
        "test_score",
        "verified",
        # "certificate_confirmed",
        "document",
        # "document_preview",
        # "modified_by",
    )
    list_editable = (
        "test_score",
        "verified",
        # "certificate_confirmed",
        # "training_class",
        # "document",
    )
    ordering = ("-updated_at",)

    fields = (
        "employee",
        "get_course",
        "training_class",
        "test_score",
        "verified",
        # "certificate_confirmed",
        "document",
        "document_preview",
        "updated_at",
        "modified_by",
    )
    readonly_fields = (
        "get_course",
        "updated_at",
        "modified_by",
        "document_preview",
    )

    list_filter = ("training_class__course",)

    @admin.display(description="Course")
    def get_course(self, obj):
        return obj.training_class.course if obj.training_class else None

    get_course.admin_order_field = "training_class__course"