from django.contrib import admin
from django.http import HttpResponseRedirect, HttpResponse
from django_admin_flexlist import FlexListAdmin
from company.models.Employees import Student, ContactsExchange
from pdf_plugin.admin_mixin import PDFGenerateMixin


# сюда подставляем копию из Employee
class StudentInline(admin.TabularInline):
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
        return super().get_queryset(request).select_related(
            "training_class__course__training_type"
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


@admin.register(ContactsExchange)
class EmployeesStudentsAdmin(PDFGenerateMixin, FlexListAdmin):
    inlines = (StudentInline,)
    list_per_page = 1
    search_fields = ()
    list_display = ()
    list_editable = ()

    def get_fields(self, request, obj=None):
        return []

    def get_readonly_fields(self, request, obj=None):
        return []

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        inline_mode = (request.GET.get("inline") == "students") or (request.POST.get("inline") == "students")
        response = super().changeform_view(request, object_id, form_url, extra_context)

        # Если это "модальная" сессия и сохранение прошло (обычно ответ — редирект)
        if inline_mode and isinstance(response, HttpResponseRedirect):
            return HttpResponse(
                """<!doctype html><meta charset="utf-8">
                <script>
                  setTimeout(function(){
                    if (window.parent) {
                      window.parent.postMessage({type:'inline-saved'}, window.location.origin);
                    }
                  }, 200);
                </script>""",
                content_type="text/html",
                status=200,
            )
        return response
