# import traceback
import json

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from company.services.EmployeesService import EmployeesService
from core.models import Fields_Settings, Saved_Filter
from core.models.FieldsSettings import Type

NUMBER_OF_COLUMNS_FOR_FILTER = 6

@staff_member_required
@csrf_exempt
def update_columns_settings(request):
    if request.method == "POST":
        type_param = request.GET.get("type")
        # if not request.user.is_superuser:
        #     return JsonResponse({"status": "Content for superuser only"}, status=400)

        if type_param not in Type.__members__:
            return JsonResponse({"status": "error"}, status=400)

        data = json.loads(request.body)
        # user = request.user
        user = User.objects.get(id=1)

        columns_settings = data.get("columns_settings", [])
        if columns_settings:
            Fields_Settings.objects.update_or_create(
                user=user,
                type=type_param,
                defaults={"fields": columns_settings}
            )
            return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error"}, status=400)


@staff_member_required
def columns_settings_view_json(request):
    type_param = request.GET.get("type")
    user_fields = EmployeesService.get_fields_for_employee_table(user=request.user, type_param=type_param)
    all_fields = EmployeesService.get_all_fields_for_employee_table()


    final_fields = []

    for field in user_fields:
        if field in all_fields:
            final_fields.append({"field_name": field, "visible": True})

    for field in all_fields:
        if field not in user_fields:
            final_fields.append({"field_name": field, "visible": False})

    return JsonResponse(final_fields, safe=False)

@staff_member_required
def columns_settings_for_filter(request, filter_id):
    columns = Saved_Filter.objects.get(id=filter_id).columns
    all_fields = EmployeesService.get_all_fields_for_employee_table()


    final_fields = []

    for field in columns:
        if field in all_fields:
            final_fields.append({"field_name": field, "visible": True})

    for field in all_fields:
        if field not in columns:
            final_fields.append({"field_name": field, "visible": False})

    return JsonResponse(final_fields, safe=False)

@staff_member_required
@csrf_exempt
def columns_settings_update_for_filter(request, filter_id):
    if request.method == "POST":
        data = json.loads(request.body)
        # user = request.user

        columns = data.get("columns", [])[:NUMBER_OF_COLUMNS_FOR_FILTER]
        if columns:
            saved_filter_instance = Saved_Filter.objects.get(id=filter_id)
            saved_filter_instance.columns = columns
            saved_filter_instance.save()
            return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error"}, status=400)