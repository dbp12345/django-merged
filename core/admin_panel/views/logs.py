# Удалил это и не пользуемся этим больше, оставил это как для примера
from django.contrib.admin.views.decorators import staff_member_required

import logging
logger = logging.getLogger(__name__)

from django.http import HttpResponse
from django.shortcuts import render

from core.models import Contacts_Prop_Logs

@staff_member_required
def logs_view(request):

    if not request.user.is_authenticated:
        return HttpResponse("You are not authorized to view this page.", status=403)

    errors_get = request.GET.get("errors", None)

    logger.info("Значение переменной: %s", errors_get)

    if errors_get == "successful":
        all_records = Contacts_Prop_Logs.objects.filter(status_code=Contacts_Prop_Logs.StatusCode.OK).order_by("-id")
    elif errors_get == "errors":
        all_records = Contacts_Prop_Logs.objects.exclude(status_code=Contacts_Prop_Logs.StatusCode.OK).order_by("-id")
    elif errors_get:
        all_records = Contacts_Prop_Logs.objects.filter(status_code=errors_get).order_by("-id")
    else:
        all_records = Contacts_Prop_Logs.objects.all().order_by("-id")



    context = {
        "title": "Logs",
        "data": all_records,
        "status_code_critical": Contacts_Prop_Logs.StatusCode.CRITICAL,
        "status_code_ok": Contacts_Prop_Logs.StatusCode.OK,
        "errors": errors_get
    }

    return render(request, "logs.html", context)
