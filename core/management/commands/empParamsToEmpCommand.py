from django.core.management.base import BaseCommand

from company.models import Employees_Parameters, Employees
from company.signals import sync_employee_core_fields_from_param, PROP_MAP

from exchange.models import Contacts_Prop

def force_resave_important_parameters():
    sync_props = [
        "MobilePhone",
        "Email",
        "given_name",
        "middle_name",
        "surname",
        "job_title"
    ]
    params = Employees_Parameters.objects.filter(
        contacts_prop__property_name__in=sync_props
    ).select_related("contacts_prop", "employee")

    for param in params:
        sync_employee_core_fields_from_param(param)


def force_clear_missing_parameters_from_employees():
    # Получаем prop_id по PROP_MAP
    PROP_MAP.pop("Email", None)
    prop_ids_by_name = {
        p.property_name: p.id
        for p in Contacts_Prop.objects.filter(property_name__in=PROP_MAP.keys())
    }

    employees = Employees.objects.all().prefetch_related("employees_parameters_entries")

    for emp in employees:
        existing_props = {
            ep.contacts_prop_id
            for ep in emp.employees_parameters_entries.all()
            if ep.contacts_prop.property_name in PROP_MAP
        }

        fields_to_clear = []
        for prop_name, model_field in PROP_MAP.items():
            expected_prop_id = prop_ids_by_name.get(prop_name)
            if expected_prop_id and expected_prop_id not in existing_props:
                if getattr(emp, model_field):  # Только если не пусто
                    setattr(emp, model_field, None)
                    fields_to_clear.append(model_field)

        if fields_to_clear:
            emp.save(update_fields=fields_to_clear)


# python manage.py empParamsToEmpCommand
class Command(BaseCommand):
    help = "Run empParamsToEmpCommand"

    def handle(self, *args, **options):
        force_resave_important_parameters()
        force_clear_missing_parameters_from_employees()
        print("END")
        exit()

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
