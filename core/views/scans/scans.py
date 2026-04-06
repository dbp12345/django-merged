from django.shortcuts import render
from django.views import View
from django.http import HttpRequest, HttpResponse

from core.models import Mqtt_Log
from core.services.MqttScansService import MqttScansService


class ScansView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        phone_name = request.GET.get("phone_name", None)
        if phone_name:
            data = list(Mqtt_Log.objects.filter(topic="crew/boss", beacon__isnull=False, phone_name=phone_name).order_by("timestamp").values_list("timestamp", "beacon"))
        else:
            data = list(Mqtt_Log.objects.filter(topic="crew/boss", beacon__isnull=False).order_by("timestamp").values_list("timestamp", "beacon"))
        row = [{"timestamp": ts, "beacon_id": beacon} for ts, beacon in data]

        res = MqttScansService.detect_visits(beacon_logs=row)

        for i in res:
            print(i)

        return render(request, "admin/scans/index.html", {
            "res": res,
        })
