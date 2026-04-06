from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseRedirect

from synchronization.services.SyncInstantService import SyncInstantService


@staff_member_required
def sync_parameters_logs_execute(request, sync_parameters_logs_id):
    if not request.user.is_authenticated:
        return JsonResponse({"errors": "You are not authorized to view this page."}, status=403)

    SyncInstantService.repeat_update_remote_contacts(sync_parameters_logs_id=sync_parameters_logs_id)

    referer = request.META.get('HTTP_REFERER')
    return HttpResponseRedirect(referer)
