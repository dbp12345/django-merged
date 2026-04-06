from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required

from core.models import Saved_Filter
from core.tasks import sync_employees_task
from privser.models import Custom_Fields
from django.conf import settings


@method_decorator(staff_member_required, name="dispatch")
class ExternalSyncView(View):
    template_name = "admin/external_sync/external_sync.html"

    def get(self, request, *args, **kwargs):
        title = "External Sync"

        filters = list(Saved_Filter.objects.values("id", "name"))

        custom_fields_instance = Custom_Fields.objects.filter(
            privser_name__isnull=False,
            exchange_property__isnull=False,
            no_sync=False
        ).order_by("privser_name")

        context = {
            "title": title,
            "filters": filters,
            "custom_fields": custom_fields_instance,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        direction = request.POST.get("direction")
        employee_filter_id = request.POST.get("employee_filter")
        selected_fields = request.POST.getlist("fields")

        print("Direction:", direction)
        print("Filter:", employee_filter_id)
        print("Selected fields:", selected_fields)

        if settings.DEBUG:
            sync_employees_task.run(direction, employee_filter_id, selected_fields)
            task_id = None
        else:
            task = sync_employees_task.delay(direction, employee_filter_id, selected_fields)
            task_id = task.id

        return JsonResponse({"status": "in_progress", "task_id": task_id})
