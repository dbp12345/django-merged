from django.core.management.base import BaseCommand

from privser.models import Contacts_Parameters
from privser.services.PrivserUpdatesService import PrivserUpdatesService


class Command(BaseCommand):
    help = "Run UpdatePictureFromPrivserCommand"

    def handle(self, *args, **options):
        param_names = [
            "G0MIEOY6M6QiManeaWw7",
            "XZi0yimkN2ekjYv8tauC",
            "Et6He1FIsCiSDwZecZuQ"
        ]

        parameters = Contacts_Parameters.objects.select_related("contacts").filter(
            name__in=param_names
        )

        grouped = {}

        for param in parameters:
            email = param.contacts.email
            if not email:
                continue

            parsed_value = parse_contacts_parameter_value(param.value)

            if not parsed_value:
                continue  # пропускаем пустые или не-словарные значения

            if email not in grouped:
                grouped[email] = {"email": email}

            grouped[email][param.name] = parsed_value

        result = list(grouped.values())

        for i in result:
            PrivserUpdatesService.save_or_update_contacts_photos_from_arr(i, False)


def parse_contacts_parameter_value(value: str):
    if not value:
        return None

    # Простой текст — не словарь
    if not value.strip().startswith("{"):
        return None

    try:
        import ast
        parsed = ast.literal_eval(value)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None
