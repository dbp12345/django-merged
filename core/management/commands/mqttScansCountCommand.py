from django.core.management.base import BaseCommand

from core.models import Mqtt_Log
from core.services.MqttScansService import MqttScansService


class Command(BaseCommand):
    help = "mqttScansCountCommand"


    def handle(self, *args, **options):
        print("-=start=-")
        data = list(Mqtt_Log.objects.filter(topic__in=("crew/boss",), beacon__isnull=False).order_by("timestamp").values_list("timestamp", "beacon"))
        row = [{"timestamp": ts, "beacon_id": beacon} for ts, beacon in data]

        # from datetime import datetime, timedelta
        # start = datetime(2025, 5, 20, 10, 0)
        #
        # row = [
        #     {"timestamp": start, "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=5), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=15), "beacon_id": "025C"},
        #
        #     {"timestamp": start + timedelta(minutes=54), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=55), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=65), "beacon_id": "025C"},
        #
        #     {"timestamp": start + timedelta(minutes=59), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=60), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=70), "beacon_id": "025C"},
        #
        #     {"timestamp": start + timedelta(minutes=64), "beacon_id": "01682"},
        #     {"timestamp": start + timedelta(minutes=65), "beacon_id": "01682"},
        #     {"timestamp": start + timedelta(minutes=75), "beacon_id": "025C2"},
        #
        #     {"timestamp": start + timedelta(minutes=74), "beacon_id": "01682"},
        #     {"timestamp": start + timedelta(minutes=75), "beacon_id": "01682"},
        #     {"timestamp": start + timedelta(minutes=85), "beacon_id": "025C2"},
        #
        #
        #
        #     {"timestamp": start + timedelta(minutes=284), "beacon_id": "01682"},
        #     {"timestamp": start + timedelta(minutes=285), "beacon_id": "01682"},
        #     {"timestamp": start + timedelta(minutes=295), "beacon_id": "025C2"},
        #
        #     {"timestamp": start + timedelta(minutes=264), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=265), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=275), "beacon_id": "025C"},
        #
        #     {"timestamp": start + timedelta(minutes=274), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=275), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=285), "beacon_id": "025C"},
        #
        #     {"timestamp": start + timedelta(minutes=284), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=285), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=295), "beacon_id": "025C"},
        #
        #
        #
        #     {"timestamp": start + timedelta(minutes=384), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=385), "beacon_id": "0168"},
        #
        #     {"timestamp": start + timedelta(minutes=364), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=365), "beacon_id": "0168"},
        #
        #     {"timestamp": start + timedelta(minutes=374), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=375), "beacon_id": "0168"},
        #
        #     {"timestamp": start + timedelta(minutes=384), "beacon_id": "0168"},
        #     {"timestamp": start + timedelta(minutes=385), "beacon_id": "0168"},
        # ]

        # print("row", row)

        res = MqttScansService.detect_visits(beacon_logs=row)

        for i in res:
            print(i)

        print("-=end=-")
