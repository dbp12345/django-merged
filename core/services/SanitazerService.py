import re
from decimal import Decimal

from dateutil.parser import parse
from datetime import datetime, timezone, date
from typing import Optional

from django.utils.timezone import make_aware, is_naive
from exchangelib import EWSDateTime, EWSTimeZone

from exchange.models import Contacts_Prop


class SanitazerService:

    # @staticmethod
    # def normalize_to_str_by_property_type_for_privser(value, property_type, output_format="%Y-%m-%d %H:%M:%S") -> str or None:
    #     if property_type == "DATE":
    #         value = int(value)
    #         value = value/1000
    #
    #         utc_zone = pytz.utc
    #         datetime_in_utc = datetime.fromtimestamp(value, utc_zone)
    #         value = datetime_in_utc.strftime(output_format)
    #         return value
    #
    #     return value

    @staticmethod
    def normalize_to_str_by_property_type_from_exchange(value, property_type, output_format="%Y-%m-%d %H:%M:%S") -> str or None:
        if property_type == Contacts_Prop.TypeChoices.SYSTEM_TIME:
            if output_format is None:
                output_format = "%Y-%m-%d %H:%M:%S"
            return SanitazerService.format_ewsdatetime_to_str(value, output_format=output_format)
        elif property_type == Contacts_Prop.TypeChoices.DOUBLE:
            if value is None:
                return None
            return str(value)
        elif property_type == Contacts_Prop.TypeChoices.STRING:
            if isinstance(value, str):
                return value.strip()

        if value is not None:
            return str(value).strip()
        else:
            return None

    @staticmethod
    def normalize_from_str_by_property_type(value, property_type=None, output_format="%Y-%m-%d %H:%M:%S"):
        if property_type == Contacts_Prop.TypeChoices.SYSTEM_TIME:
            return SanitazerService.datetime_str_to_datetime(value)
            # if isinstance(value, datetime):
            #     return value
            # if output_format is None:
            #     output_format = "%Y-%m-%d %H:%M:%S"
            # # output_format - правильно надо было бы переименовать в input_format
            # return datetime.strptime(value, output_format) #дата со временем
            # # return datetime.strptime(value, output_format).date() #дата без времени
        elif property_type == Contacts_Prop.TypeChoices.BOOL:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in ["true", "1", "yes", "on"]
            if isinstance(value, (int, float)):
                return value != 0
            return False
        elif property_type == Contacts_Prop.TypeChoices.DOUBLE:
            try:
                return Decimal(str(value).strip())
            except Exception:
                return None
        if value is not None:
            return str(value).strip()
        else:
            return None

    @staticmethod
    def convert_date_format_str(value, from_format=None, output_format=None) -> str:
        if from_format and output_format:
            return datetime.strptime(value, from_format).strftime(output_format)
        return value

    @staticmethod
    def normalize_to_str_by_property_type_for_exchange(value, property_type) -> str or None:
        if property_type == Contacts_Prop.TypeChoices.SYSTEM_TIME:
            return SanitazerService.datetime_str_to_ewsdatetime(value)
        elif property_type == Contacts_Prop.TypeChoices.DOUBLE:
            try:
                return Decimal(str(value).strip())
            except Exception as e:
                from core.exceptions import StopTask
                from synchronization.models import Sync_Delivery_Logs
                raise StopTask(f"Invalid decimal value: {value!r} — {e}", status_code=Sync_Delivery_Logs.StatusCode.CANCELED.value)
        elif property_type == Contacts_Prop.TypeChoices.STRING:
            if value:
                return str(value)
            else:
                return ""
        return value

    @staticmethod
    def normalize_to_str_or_none(value, output_format="%Y-%m-%d %H:%M:%S") -> str or None:
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, Decimal):
            return str(value)
        value = SanitazerService.format_ewsdatetime_to_str(value)
        value = SanitazerService.check_datetime_str_to_str(value, output_format)
        return value

    @staticmethod
    def format_ewsdatetime_to_str(value, output_format="%Y-%m-%d %H:%M:%S") -> str or None:
        if value is None or value == "":
            return None
        if value.year > 3000:
            return None
        return SanitazerService.format_ewsdatetime_to_datetime(value).strftime(output_format)

    @staticmethod
    def format_ewsdatetime_to_datetime(value) -> str or None:
        if value is None or value == "":
            return None

        if isinstance(value, EWSDateTime):
            value = value.astimezone()  # Преобразование в datetime (учитывая часовой пояс)
            if value.year > 3000:
                return None
            return datetime(
                year=value.year,
                month=value.month,
                day=value.day,
                hour=value.hour,
                minute=value.minute,
                second=value.second,
                microsecond=value.microsecond,
                tzinfo=value.tzinfo
            )

        return None

    @staticmethod
    def check_datetime_str_to_str(input_string, output_format):
        if input_string is None or input_string == "":
            return None
        try:
            pattern = r"(\d{4}[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12][0-9]|3[01])|(0?[1-9]|[12][0-9]|3[01])[-/](0?[1-9]|1[0-2])[-/]\d{4}|(0?[1-9]|1[0-2])[-/](0?[1-9]|[12][0-9]|3[01])[-/]\d{4})"

            match = re.search(pattern, input_string)
            if match:
                parsed_date = parse(input_string, fuzzy=False)
                return parsed_date.strftime(output_format)
            else:
                return input_string
        except Exception as e:
            return input_string

    @staticmethod
    def datetime_str_to_ewsdatetime(input_string):
        if input_string is None or input_string == "":
            return None
        value = SanitazerService.datetime_str_to_datetime(input_string)
        return SanitazerService.datetime_to_ewsdatetime(value)

    @staticmethod
    def datetime_to_ewsdatetime(value):
        if isinstance(value, date) and not isinstance(value, datetime):
            value = datetime.combine(value, datetime.min.time())

        utc_tz = EWSTimeZone.localzone()

        try:
            ews_datetime = EWSDateTime(
                year=value.year,
                month=value.month,
                day=value.day,
                hour=value.hour,
                minute=value.minute,
                second=value.second,
                tzinfo=utc_tz
            )
            return ews_datetime
        except Exception as e:
            from core.exceptions import StopTask
            from synchronization.models import Sync_Delivery_Logs
            raise StopTask(str(e), status_code=Sync_Delivery_Logs.StatusCode.CANCELED.value)

    @staticmethod
    def datetime_str_to_datetime(input_string):
        if not input_string:
            return None

        if isinstance(input_string, datetime):
            return make_aware(input_string) if is_naive(input_string) else input_string

        if isinstance(input_string, date):
            return make_aware(datetime.combine(input_string, datetime.min.time()))

        # Try ISO format with timezone (e.g. '2025-06-13 00:00:00-07:00')
        try:
            dt = datetime.fromisoformat(input_string)
            return dt if dt.tzinfo else make_aware(dt)
        except ValueError:
            pass

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%m-%d-%Y %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
            "%m-%d-%Y",
            "%m/%d/%Y",
            "%Y-%m-%d",
            "%Y/%m/%d",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(input_string, fmt)
                return make_aware(dt)
            except ValueError:
                continue

        return None

    @staticmethod
    def datetime_str_to_datetime_OLD(input_string):
        if not input_string:  # Check for empty or None input
            return None

        if isinstance(input_string, date):
            return input_string

        # Define supported formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%m-%d-%Y %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
            "%m-%d-%Y",
            "%m/%d/%Y",
            "%Y-%m-%d",
            "%Y/%m/%d",
        ]

        for fmt in formats:
            try:
                parsed_datetime = datetime.strptime(input_string, fmt)
                return make_aware(parsed_datetime)
            except ValueError:
                continue  # Try the next format

        return None

    # @staticmethod
    # def datetime_to_datetime_str(input_string):
    #
    #     if input_string is None or input_string == "":
    #         return None
    #     input_string = datetime.strptime(input_string, "%Y-%m-%d %H:%M:%S")
    #     return make_aware(input_string)

    @staticmethod
    def format_phone_sanitize_to_str(value) -> str or None:
        if value is None:
            return None
        value = re.sub(r"[\s\-\(\)\+]", "", value)
        value = value[-10:]
        return value if value else None

    @staticmethod
    def contains_phone(fullphone: str, subphone: str) -> bool:
        subphone = SanitazerService.format_phone_sanitize_to_str(subphone)
        fullphone = SanitazerService.format_phone_sanitize_to_str(fullphone)
        if subphone is None and fullphone is None:
            return True
        if subphone is None or fullphone is None:
            return False
        return subphone in fullphone or fullphone in subphone

    @staticmethod
    def safe_make_aware(dt: datetime) -> datetime:
        if dt is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        if is_naive(dt):
            return make_aware(dt)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def parse_iso_date_to_date(s: Optional[str]):
        """Принимает '2025-09-08T00:00:00Z' -> возвращает date() или None."""
        if not s:
            return None
        try:
            # fromisoformat не понимает 'Z'
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        except Exception:
            try:
                return datetime.strptime(s.split("T")[0], "%Y-%m-%d").date()
            except Exception:
                return None
