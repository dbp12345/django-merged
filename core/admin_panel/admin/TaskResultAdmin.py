from django.contrib import admin
from django_admin_flexlist import FlexListAdmin
from django_celery_results.models import TaskResult
from django.db.models import Count
from pdf_plugin.admin_mixin import PDFGenerateMixin

admin.site.unregister(TaskResult)


class TaskStateFilter(admin.SimpleListFilter):
    title = "My Task State"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        statuses = TaskResult.objects.values("status").annotate(count=Count("status"))
        return [(status["status"], f"{status["status"]} ({status["count"]})") for status in statuses]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(TaskResult)
class TaskResultAdmin(PDFGenerateMixin, FlexListAdmin):
    list_display = (
        "task_id",
        "periodic_task_name",
        "task_name",
        "date_done",
        "status",
        "worker"
    )
    # list_filter = (TaskStateFilter,)
    list_filter = (
        TaskStateFilter,
        "status",
        "date_done",
        "periodic_task_name",
        "task_name",
        "worker"
    )
    ordering = ("-date_done",)

    date_hierarchy = "date_done"
    readonly_fields = (
        "date_created",
        "date_done",
        "result",
        "meta"
    )
    search_fields = (
        "task_name",
        "task_id",
        "status",
        "task_args",
        "task_kwargs",
        "result"
    )
