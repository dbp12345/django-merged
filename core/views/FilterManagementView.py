import json
from urllib.parse import urlencode

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt

from company.services.EmployeesService import EmployeesService
from core.models import Saved_Filter, Saved_Filter_Order
from core.models.FieldsSettings import Type


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(staff_member_required, name="dispatch")
class FilterManagementView(View):
    def get(self, request, *args, **kwargs):
        """ Get saved filters with querystring-ready params """
        filters = Saved_Filter.objects.all()
        data = [
            {
                "id": f.id,
                "name": f.name,
                "params": urlencode(f.params),
            }
            for f in filters
        ]
        return JsonResponse(data, safe=False)

    def post(self, request, *args, **kwargs):
        """ Save new filter """
        try:
            filter_name = request.POST.get("name")
            or_filter_groups = {k: v for k, v in request.POST.items() if "f_" in k}
            or_filter_groups['f_name'] = filter_name
            if not filter_name or not or_filter_groups:
                return JsonResponse({"status": "error", "message": "Filter name and parameters are required"}, status=400)

            # if Saved_Filter.objects.filter(name=filter_name).exists():
            #     return JsonResponse({"status": "error", "message": "A filter with this name already exists"}, status=400)
            # Saved_Filter.objects.create(name=filter_name, params=or_filter_groups)

            all_params = EmployeesService.get_fields_for_employee_table(user=request.user, type_param=Type.EMPLOYEES_AJAX.name)

            Saved_Filter.objects.update_or_create(
                name=filter_name,
                defaults={"params": or_filter_groups, "columns_main": all_params}
            )
            return JsonResponse({"status": "success"})

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "JSON processing error"}, status=400)
        except IntegrityError:
            return JsonResponse({"status": "error", "message": "Filter save error"}, status=500)

    def delete(self, request, *args, **kwargs):
        """ Delete filter """
        try:
            data = json.loads(request.body)
            filter_id = data.get("id")

            if not filter_id:
                return JsonResponse({"status": "error", "message": "Filter ID is required"}, status=400)

            deleted, _ = Saved_Filter.objects.filter(id=filter_id).delete()
            if deleted:
                return JsonResponse({"status": "success"})
            return JsonResponse({"status": "error", "message": "Filter not found"}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "JSON processing error"}, status=400)

@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(staff_member_required, name="dispatch")
class FilterManagementOrderView(View):
    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            data = json.loads(request.body)
            user = request.user

            obj, created = Saved_Filter_Order.objects.get_or_create(
                user=user,
                defaults={"order": data}
            )

            if not created:
                obj.order = data
                obj.save()
            return JsonResponse({"status": "ok"})
        return JsonResponse({"status": "error"}, status=400)
