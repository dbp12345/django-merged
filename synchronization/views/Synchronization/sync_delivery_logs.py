from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseRedirect
from core.tasks import handle_sync_delivery_log_task


@staff_member_required
def sync_delivery_logs_execute(request, sync_delivery_logs_id):
    if not request.user.is_authenticated:
        return JsonResponse({"errors": "You are not authorized to view this page."}, status=403)

    if settings.DEBUG:
        handle_sync_delivery_log_task.run(sync_delivery_logs_id)
    else:
        handle_sync_delivery_log_task.delay(sync_delivery_logs_id) #good

    referer = request.META.get('HTTP_REFERER')
    return HttpResponseRedirect(referer)
