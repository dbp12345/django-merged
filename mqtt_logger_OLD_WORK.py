import paho.mqtt.client as mqtt
import json
import django
import os

from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

mqtt_host = settings.MQTT_HOST
mqtt_user = settings.MQTT_USER
mqtt_pass = settings.MQTT_PASS

from django.utils.timezone import now
from core.models import Mqtt_Log
import logging
from datetime import datetime, UTC

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe("#")  # подписка на все топики, можешь ограничить


logger = logging.getLogger("my_mqtt")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        logger.debug(f"{now()} | {now().isoformat()}")
        logger.debug(f"Topic: {msg.topic} | Data: {payload}")

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            parsed = None

        condition = parsed.get("conditionContent") if parsed else None
        raw_timestamp = parsed.get("currentTimestamp") if parsed else None
        device_name = parsed.get("deviceName") if parsed else None

        dt = None
        if raw_timestamp:
            try:
                dt = datetime.fromtimestamp(raw_timestamp, UTC)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid timestamp: {raw_timestamp} | {e}")

        if isinstance(condition, list):
            for beacon in condition:
                Mqtt_Log.objects.create(
                    topic=msg.topic,
                    raw_data=payload,
                    parsed_data=parsed,
                    timestamp=dt,
                    raw_timestamp=raw_timestamp,
                    phone=device_name,
                    beacon=beacon,
                )
        else:
            Mqtt_Log.objects.create(
                topic=msg.topic,
                raw_data=payload,
                parsed_data=parsed,
                timestamp=dt,
                raw_timestamp=raw_timestamp,
                phone=device_name,
                beacon=None,
            )

    except Exception as e:
        logger.error(f"Unhandled error in on_message: {e}")
        print("Error:", e)

def on_disconnect(client, userdata, rc):
    logger.warning(f"Disconnected from MQTT broker. Code: {rc}")

client = mqtt.Client()
client.username_pw_set(mqtt_user, mqtt_pass)
# client.username_pw_set(os.getenv("MQTT_USER"), os.getenv("MQTT_PASS"))
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.connect(mqtt_host, 1883, 60)
client.loop_forever()
