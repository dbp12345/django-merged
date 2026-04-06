from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponseRedirect

from company.models import Employees
from exchange.services.ExchangeUpdatesService import ExchangeUpdatesService


@staff_member_required
def update_contact_from_exchange_by_email(request, obj_id):
    if not request.user.is_authenticated:
        return JsonResponse({"errors": "You are not authorized to view this page."}, status=403)

    if settings.DEBUG:
        ExchangeUpdatesService.do_update_from_exchange_by_email(email=Employees.objects.get(id=obj_id).email, ignore_diff_properties=False)
    else:
        try:
            ExchangeUpdatesService.do_update_from_exchange_by_email(email=Employees.objects.get(id=obj_id).email, ignore_diff_properties=False)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=500)

    referer = request.META.get('HTTP_REFERER')
    return HttpResponseRedirect(referer)
