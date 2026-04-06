from django.views import View
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render

from company.models import Employees
from paychex.services.PaychexService import PaychexService


class PaychexTestView(View):
    def get(self, request, *args, **kwargs):
        employee = Employees.objects.get(id=25973)

        res = PaychexService.create_progress_worker_in_paychex(employee=employee)

        if isinstance(res, dict) and isinstance(res.get("content"), list):
            first = res["content"][0] if res["content"] else None
            if first and "workerId" in first and "name" in first:
                return JsonResponse(res)

        return JsonResponse(res)
        return JsonResponse({"error": "Invalid response from Paychex"}, status=400)

        # обработка GET-запроса
        context = {"key": "value"}
        return render(request, "app/template.html", context)

    def post(self, request, *args, **kwargs):
        # обработка POST-запроса
        data = request.POST.get("param")
        if not data:
            return HttpResponseBadRequest("Missing 'param'")
        return JsonResponse({"received": data})
