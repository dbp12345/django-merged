# from django.contrib.admin.views.decorators import staff_member_required
# from django.http import JsonResponse, HttpResponseRedirect
# from synchronization.models import Sync
# from synchronization.services.SyncService import SyncService
#
# @staff_member_required
# def sync_update_all_by_email(request, obj_id):
#     if not request.user.is_authenticated:
#         return JsonResponse({"errors": "You are not authorized to view this page."}, status=403)
#
#     SyncService.update_all_sync_by_email(Sync.objects.get(id=obj_id).email)
#
#     referer = request.META.get('HTTP_REFERER')
#     return HttpResponseRedirect(referer)
