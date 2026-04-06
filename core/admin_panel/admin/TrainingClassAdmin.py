from datetime import datetime

from django.contrib import admin
from django.db.models import Q
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import TrainingClass, Student
from pdf_plugin.admin_mixin import PDFGenerateMixin


class StudentInline(admin.TabularInline):
    show_change_link = False
    model = Student
    autocomplete_fields = ("employee",)
    fields = (
        # "updated_at_link",
        "employee",
        "training_class",
        "test_score",
        "verified",
        "document_preview",
        "document",
        # "updated_at",
        # "modified_by",
    )
    readonly_fields = (
        # "updated_at_link",
        # "employee",
        # "test_score",
        # "training_class",
        # "document",
        "document_preview",
        # "updated_at",
        # "modified_by",
    )
    extra = 0
    can_delete = True
    ordering = ("-updated_at",)

    # def updated_at_link(self, instance):
    #     url = reverse("admin:%s_%s_change" % (instance._meta.app_label, instance._meta.model_name),
    #  args=[instance.id])
    #     return format_html('<a href="{}">{}</a>', url, instance.updated_at.strftime('%m/%d/%Y %H:%M'))
    #
    # updated_at_link.short_description = "Updated At"


@admin.register(TrainingClass)
class TrainingClassAdmin(PDFGenerateMixin, FlexListAdmin):
    # def has_add_permission(self, request):
    #     return False
    # def has_delete_permission(self, request, obj=None):
    #     return False
    autocomplete_fields = ("course", "instructor")
    list_per_page = 50
    search_fields = ("instructor__email", "date", "course__training_type__name", "location")

    def get_search_results(self, request, queryset, search_term):
        # просто проба сделать поиск по дурацкой американской дате
        filters = Q()

        # Попытка: MM/DD/YYYY
        try:
            date_obj = datetime.strptime(search_term, "%m/%d/%Y").date()
            filters |= Q(date=date_obj)
        except ValueError:
            pass

        # Попытка: MM/YYYY
        try:
            date_obj = datetime.strptime(search_term, "%m/%Y")
            filters |= Q(date__year=date_obj.year, date__month=date_obj.month)
        except ValueError:
            pass

        # Попытка: YYYY
        try:
            year = int(search_term)
            filters |= Q(date__year=year)
        except ValueError:
            pass

        # Попытка: одно число — ищем по году, месяцу, дню
        try:
            single_number = int(search_term)
            filters |= Q(date__year=single_number) | Q(date__month=single_number) | Q(date__day=single_number)
        except ValueError:
            pass

        if filters:
            queryset = queryset.filter(filters)
            return queryset, False

        return super().get_search_results(request, queryset, search_term)

    list_display = (
        # "employee",
        "date",
        "course",
        "association",
        "instructor",
        "test_score",
        "location",
        "document",
        # "document_preview",
        "students_count",
    )
    list_editable = (
        "course",
        "association",
        "test_score",
        "location",
        # "document",
    )
    ordering = ("-date",)

    fields = (
        # "employee",
        "instructor",
        "course",
        "association",
        "test_score",
        "date",
        "location",
        "document",
        "document_preview",
        "updated_at",
        "modified_by",
        "students_count",
    )
    readonly_fields = (
        # "employee",
        "updated_at",
        "modified_by",
        "document_preview",
        "students_count",
    )

    list_filter = ("course",)

    inlines = (
        StudentInline,
    )

    @admin.display(description="Students Count")
    def students_count(self, obj):
        return obj.student_entries.count()
