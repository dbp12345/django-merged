import os
import json
import logging
from datetime import datetime, UTC
from django.utils.dateparse import parse_datetime

# Django init must be before importing settings/models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

from django.conf import settings
from django.db import close_old_connections
from django.utils.timezone import now

import paho.mqtt.client as mqtt

from core.models import Mqtt_Log

logger = logging.getLogger("my_mqtt")

mqtt_host = settings.MQTT_HOST
mqtt_user = settings.MQTT_USER
mqtt_pass = settings.MQTT_PASS


def _to_dt(ts):
    if ts is None:
        return None
    try:
        # epoch as number or numeric string
        val = float(ts)
        if val > 1e12:
            val = val / 1000.0
        return datetime.fromtimestamp(val, UTC)
    except Exception:
        # try ISO-8601
        if isinstance(ts, str):
            dt = parse_datetime(ts)
            if dt is not None:
                return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
        logger.warning(f"Invalid timestamp: {ts}")
        return None


def on_connect(client, userdata, flags, rc):
    logger.info(f"Connected to MQTT with code={rc}")
    client.subscribe("#")


def on_disconnect(client, userdata, rc):
    logger.warning(f"Disconnected from MQTT broker. Code: {rc}")


def on_message(client, userdata, msg):
    # Protect against stale DB connections in long-running process
    close_old_connections()
    try:
        payload = msg.payload.decode(errors="replace")
        logger.debug(f"{now()} | Topic: {msg.topic} | Data: {payload}")

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            parsed = None

        condition = parsed.get("conditionContent") if parsed else None
        raw_timestamp = parsed.get("currentTimestamp") if parsed else None
        device_name = parsed.get("deviceName") if parsed else None

        dt = _to_dt(raw_timestamp)

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
        logger.error(f"Unhandled error in on_message: {e}", exc_info=True)


# ---- MQTT client bootstrap ----
# Compatibility with both paho-mqtt v1 and v2
if hasattr(mqtt, "CallbackAPIVersion"):
    # paho-mqtt v2: force v1 callback signatures
    client = mqtt.Client(
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1,  # <-- change vs stock
    )
else:
    # paho-mqtt v1
    client = mqtt.Client(protocol=mqtt.MQTTv311)

if mqtt_user:
    client.username_pw_set(mqtt_user, mqtt_pass)

client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Backoff for reconnects
client.reconnect_delay_set(min_delay=1, max_delay=30)

client.connect(mqtt_host, 1883, 60)
client.loop_forever()
