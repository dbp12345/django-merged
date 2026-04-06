from core.models import Mqtt_Log


class MqttScansService:

    @staticmethod
    def detect_visits(beacon_logs, min_pings=3, min_duration=15, min_gap=30, work_hours=(0, 24), min_time_between_visits=60):
        """
        beacon_logs: список словарей с ключами ['timestamp', 'beacon_id']
        Данные должны быть только по одному телефону. Отсортированы по времени.
        """

        visits = []
        last_visit_times = {}  # frozenset(beacon_ids) -> timestamp of last visit

        # Убедимся, что отсортировано по времени
        beacon_logs.sort(key=lambda x: x['timestamp'])

        session = []
        session_start = None
        last_ping_time = None

        for row in beacon_logs:
            time = row['timestamp']

            if not (work_hours[0] <= time.hour < work_hours[1]):
                continue

            if session_start is None:
                session_start = time
                last_ping_time = time
                session = [row]
                continue

            if (time - last_ping_time).total_seconds() > min_gap * 60:
                duration = (last_ping_time - session_start).total_seconds() / 60
                if duration >= min_duration and len(session) >= min_pings:
                    beacons_in_session = set(log['beacon_id'] for log in session)
                    key = frozenset(beacons_in_session)
                    last_time = last_visit_times.get(key)

                    if not last_time or (session_start - last_time).total_seconds() / 60 >= min_time_between_visits:
                        visits.append({
                            'beacons': list(beacons_in_session),
                            'start_time': session_start,
                            'end_time': last_ping_time,
                            'duration': duration
                        })
                        last_visit_times[key] = session_start

                # Новая сессия
                session_start = time
                session = [row]
            else:
                session.append(row)

            last_ping_time = time

        # Финальная сессия
        if session:
            duration = (last_ping_time - session_start).total_seconds() / 60
            if duration >= min_duration and len(session) >= min_pings:
                beacons_in_session = set(log['beacon_id'] for log in session)
                key = frozenset(beacons_in_session)
                last_time = last_visit_times.get(key)

                if not last_time or (session_start - last_time).total_seconds() / 60 >= min_time_between_visits:
                    visits.append({
                        'beacons': list(beacons_in_session),
                        'start_time': session_start,
                        'end_time': last_ping_time,
                        'duration': duration
                    })

        return visits

    @staticmethod
    def getBeacons():
        Mqtt_Log.objects.filter()