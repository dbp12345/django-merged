import json

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from core.models import Saved_Filter

@method_decorator(staff_member_required, name="dispatch")
class SettingsView(View):
    def get(self, request, *args, **kwargs):
        filters = Saved_Filter.objects.values("id", "name", "order")
        return JsonResponse(list(filters), safe=False)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            order = data.get("order", [])
            for index, filter_id in enumerate(order):
                Saved_Filter.objects.filter(id=filter_id).update(order=index)
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

