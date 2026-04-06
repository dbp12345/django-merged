import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from django.conf import settings
from django.core.cache import cache


class FlexTimeTWS:
    def __init__(self):
        self.base_url_v2 = str(settings.FLEXTIME_BASE_URL).rstrip("/")
        # build v1 from v2
        if self.base_url_v2.endswith("/2.0"):
            self.base_url_v1 = self.base_url_v2[:-4] + "/1.0"
        else:
            self.base_url_v1 = self.base_url_v2.replace("/ws-json/2.0", "/ws-json/1.0")

        self.customer_alias = settings.FLEXTIME_CUSTOMER_ALIAS
        self.shared_key = settings.FLEXTIME_SHARED_KEY
        self.wsuser = "wsuser"
        self.wspass = settings.FLEXTIME_WSPASS
        self.tz = ZoneInfo(str(settings.FLEXTIME_TZ)) if settings.FLEXTIME_TZ else timezone.utc

        # TTL must be int to avoid redis errors
        try:
            self.cache_ttl = int(settings.FLEXTIME_TOKEN_TTL or 5400)
        except Exception:
            self.cache_ttl = 5400

        self.cache_key = f"flextime:tws_token:{self.customer_alias}"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
        self.timeout = 30

        self._token = None

    # --- helpers
    @staticmethod
    def _to_epoch_ms(dt: datetime) -> int:
        if dt.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware")
        return int(dt.timestamp() * 1000)

    @staticmethod
    def _wrap_ms(ms: int) -> str:
        return f"/Date({ms})/"

    def _post(self, url: str, payload: dict):
        resp = self.session.post(url, data=json.dumps(payload), timeout=self.timeout)
        # Не поднимаем исключение по статусу: вернем тело как есть
        ct = resp.headers.get("Content-Type", "")
        if "application/json" in ct:
            return resp.json()
        # Иногда сервис возвращает HTML с ошибкой, вернем текст чтобы ты видел причину
        return {"status": resp.status_code, "content_type": ct, "text": resp.text}

    # --- auth
    def _create_token(self, force: bool = False):
        if not force:
            cached = cache.get(self.cache_key)
            if cached:
                self._token = cached
                return

        url = f"{self.base_url_v2}/CreateToken"
        payload = {
            "CustomerAlias": str(self.customer_alias),
            "SharedKey": str(self.shared_key),
            "UserName": self.wsuser,
            "UserPass": str(self.wspass),
        }
        data = self._post(url, payload)

        # if error object returned
        if isinstance(data, dict) and data.get("ErrorCode"):
            raise RuntimeError(f"TWS CreateToken error: {data.get('ErrorCode')}: {data.get('Message')}")

        # expected: token as raw JSON string (e.g. "TOKEN...") or plain string
        if isinstance(data, str) and data:
            token = data.strip('"')
            self._token = token
            cache.set(self.cache_key, self._token, timeout=self.cache_ttl)
            return

        # sometimes service returns {"status":..., "text": "...html..."}
        raise RuntimeError(f"TWS CreateToken unexpected response: {data!r}")

    # --- punches
    def get_punches_by_emp_ids(self, emp_ids, start_dt: datetime, end_dt: datetime,
                               ignore_labor: bool = True, search_action: int = 0):
        if not self._token:
            self._create_token()

        # normalize to UTC
        s_utc = start_dt.astimezone(timezone.utc)
        e_utc = end_dt.astimezone(timezone.utc)

        payload = {
            "AuthToken": self._token,
            "EmpIdentifierList": [str(x) for x in emp_ids],
            "StartDate": self._wrap_ms(self._to_epoch_ms(s_utc)),
            "EndDate": self._wrap_ms(self._to_epoch_ms(e_utc)),
            "IgnoreLaborLevelCodes": bool(ignore_labor),
            "SearchAction": int(search_action),
        }
        url = f"{self.base_url_v1}/TimeGetPunchesByEmpIdentifier"
        return self._post(url, payload)

    def get_punches_for_local_day(self, emp_ids, local_dt: datetime):
        # local_dt must be timezone-aware (or use self.tz)
        if local_dt.tzinfo is None:
            # assume service tz if caller passed naive
            local_dt = local_dt.replace(tzinfo=self.tz)
        day_start = datetime(local_dt.year, local_dt.month, local_dt.day, 0, 0, 0, tzinfo=self.tz)
        day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999000)
        return self.get_punches_by_emp_ids(emp_ids, day_start, day_end)

    # --- response helpers ---
    @staticmethod
    def _extract_rows(resp):
        # Нормализует ответ в список записей или бросает понятную ошибку.
        if isinstance(resp, list):
            return resp

        if isinstance(resp, dict):
            # возможные обертки, которые видел в реальности
            for k in ("Punches", "Result", "Data", "content"):
                v = resp.get(k)
                if isinstance(v, list):
                    return v

            # явные ошибки от сервиса — лучше поднять, чтобы caller видел причину
            if any(k in resp for k in ("ErrorCode", "status", "text")):
                raise RuntimeError(f"FlexTime error: {resp}")

        # неожиданный формат — лучше знать об этом сразу
        raise RuntimeError(f"Unexpected response shape: {type(resp)}")

    def _apply_to_date_is_today(self, row, tz: ZoneInfo):
        s = row.get("ApplyToDate")  # "MM/DD/YYYY"
        if not s:
            return False
        try:
            d = datetime.strptime(s, "%m/%d/%Y").date()
            return d == datetime.now(tz).date()
        except Exception:
            return False


        today_rows.sort(key=key)
        last = today_rows[-1]
        last_out = last if (last.get("OutTime") and str(last.get("OutTime")).strip()) else None
        return (last, last_out)

    def _is_online_today(self, rows, tz: ZoneInfo):
        for r in rows:
            if not self._apply_to_date_is_today(r, tz):
                continue
            out = (r.get("OutTime") or "").strip()
            if out == "":
                return True
        return False
