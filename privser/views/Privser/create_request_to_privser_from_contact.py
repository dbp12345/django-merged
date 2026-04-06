from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseRedirect

from company.models import Employees
from privser.services.PrivserService import PrivserService


@staff_member_required
def create_request_to_privser_from_contact(request, obj_id):
    if not request.user.is_authenticated:
        return JsonResponse({"errors": "You are not authorized to view this page."}, status=403)

    privser_service = PrivserService()
    privser_service.create_request_to_privser_from_contact(Employees.objects.get(id=obj_id))

    referer = request.META.get('HTTP_REFERER', '/admin/exchange/contacts/')
    return HttpResponseRedirect(referer)
