from datetime import datetime

from django.core.management.base import BaseCommand

from company.models import Employees_Parameters

from django.db import transaction


# python manage.py valueToDateForSystemTimeCommand
class Command(BaseCommand):
    help = "Run valueToDateForSystemTimeCommand"

    def handle(self, *args, **options):

        with transaction.atomic():
            params = Employees_Parameters.objects.select_related("contacts_prop").all()

            for param in params:
                if param.contacts_prop.property_type == "SystemTime" and param.value and not param.value_date:
                    # if param.contacts_prop.id in(15, 40):
                    try:
                        # datetime_format = param.contacts_prop.datetime_format
                        # param.value_date = datetime.strptime(param.value, datetime_format)

                        from core.services.SanitazerService import SanitazerService
                        parsed = SanitazerService.normalize_from_str_by_property_type(
                            value=param.value,
                            property_type=param.contacts_prop.property_type,
                            output_format=param.contacts_prop.datetime_format
                        )
                        if isinstance(parsed, datetime):
                            param.value_date = parsed
                        else:
                            param.value_date = None

                    except (ValueError, TypeError):
                        param.value_date = None  # Если формат неправильный или значение пустое

                    param.save(update_fields=["value_date"])

        print("END")
        exit()

"""
SELECT cp.property_name,
       COUNT(ep.id)         AS total_with_value,
       COUNT(ep.value_date) AS total_with_value_date,
       ROUND(100.0 * COUNT(ep.value_date) / COUNT(ep.id), 2) AS success_percent
FROM company_employees_parameters ep
         JOIN exchange_contacts_prop cp ON ep.contacts_prop_id = cp.id
WHERE cp.property_type = 'SystemTime'
  AND ep.value IS NOT NULL
  AND ep.value != ''
GROUP BY cp.property_name
ORDER BY total_with_value DESC;
"""
"""
SELECT e.id AS employee_id,
       e.phone AS emp_phone,
       ep_phone.value AS param_phone,
#        e.email AS emp_email,
#        ep_email.value AS param_email,
       e.first_name AS emp_first_name,
       ep_first.value AS param_first_name,
       e.middle_name AS emp_middle_name,
       ep_middle.value AS param_middle_name,
       e.last_name AS emp_last_name,
       ep_last.value AS param_last_name,
       e.job_title AS emp_job_title,
       ep_job.value AS param_job_title
FROM company_employees e
LEFT JOIN company_employees_parameters ep_phone
  ON ep_phone.employees_id = e.id AND ep_phone.contacts_prop_id = (
      SELECT id FROM exchange_contacts_prop WHERE property_name = 'MobilePhone' LIMIT 1
)
# LEFT JOIN company_employees_parameters ep_email
#   ON ep_email.employees_id = e.id AND ep_email.contacts_prop_id = (
#       SELECT id FROM exchange_contacts_prop WHERE property_name = 'Email' LIMIT 1
# )
LEFT JOIN company_employees_parameters ep_first
  ON ep_first.employees_id = e.id AND ep_first.contacts_prop_id = (
      SELECT id FROM exchange_contacts_prop WHERE property_name = 'given_name' LIMIT 1
)
LEFT JOIN company_employees_parameters ep_middle
  ON ep_middle.employees_id = e.id AND ep_middle.contacts_prop_id = (
      SELECT id FROM exchange_contacts_prop WHERE property_name = 'middle_name' LIMIT 1
)
LEFT JOIN company_employees_parameters ep_last
  ON ep_last.employees_id = e.id AND ep_last.contacts_prop_id = (
      SELECT id FROM exchange_contacts_prop WHERE property_name = 'surname' LIMIT 1
)
LEFT JOIN company_employees_parameters ep_job
  ON ep_job.employees_id = e.id AND ep_job.contacts_prop_id = (
      SELECT id FROM exchange_contacts_prop WHERE property_name = 'job_title' LIMIT 1
)
WHERE
    COALESCE(e.phone, '')     <> COALESCE(ep_phone.value, '')
#  OR COALESCE(e.email, '')     <> COALESCE(ep_email.value, '')
 OR COALESCE(e.first_name, '')<> COALESCE(ep_first.value, '')
 OR COALESCE(e.middle_name, '')<> COALESCE(ep_middle.value, '')
 OR COALESCE(e.last_name, '') <> COALESCE(ep_last.value, '')
 OR COALESCE(e.job_title, '') <> COALESCE(ep_job.value, '');
"""