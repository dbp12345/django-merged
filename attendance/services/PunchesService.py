from attendance.models import Punch_Event


class PunchesService:

    def build_sessions_from_punches(punches: Punch_Event):
        punches = sorted(punches, key=lambda p: p.timestamp)
        sessions = []
        i = 0
        while i < len(punches):
            if punches[i].event_type == "CLOCK_IN":
                j = i + 1
                while j < len(punches) and punches[j].event_type != "CLOCK_OUT":
                    j += 1
                if j < len(punches):
                    start = punches[i].timestamp
                    end = punches[j].timestamp
                    duration = int((end - start).total_seconds())
                    sessions.append((start, end, duration))
                    i = j + 1
                else:
                    sessions.append((punches[i].timestamp, None, None))  # открытая сессия
                    break
            else:
                i += 1
        return sessions
