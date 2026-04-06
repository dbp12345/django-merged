import requests
from django.conf import settings

from company.models import Employee_Change_Queue
from core.task_toggle import is_task_enabled

url_sent_changed_parameters = settings.URL_SENT_CHANGED_PARAMETERS

class ChangedParametersService:

    @staticmethod
    def send_grouped_changes():
        unsent = Employee_Change_Queue.objects.select_related('employee', 'contacts_prop').filter(
            status=Employee_Change_Queue.StatusCode.NEW
        )
        grouped = {}

        for unsent_i in unsent:
            grouped.setdefault(unsent_i.employee.id, {"employee": unsent_i.employee, "changes": []})
            grouped[unsent_i.employee.id]["changes"].append(unsent_i)

        for employee_id, data in grouped.items():
            employee = data["employee"]
            changes = data["changes"]

            payload = {
                "employee_id": employee_id,
                "email": employee.email,
                "changes": [
                    {"field": c.contacts_prop.property_name, "new_value": c.new_value} for c in changes
                ]
            }

            # print("payload", payload)

            try:
                if not is_task_enabled("change_queue_send_grouped_changes"):
                    Employee_Change_Queue.objects.filter(id__in=[c.id for c in changes]).update(
                        status=Employee_Change_Queue.StatusCode.CANCELED,
                        error_message=None
                    )
                    return

                response = requests.post(url_sent_changed_parameters, json=payload)
                if response.ok:
                    Employee_Change_Queue.objects.filter(id__in=[c.id for c in changes]).update(
                        status=Employee_Change_Queue.StatusCode.COMPLETED,
                        error_message=None
                    )
                else:
                    Employee_Change_Queue.objects.filter(id__in=[c.id for c in changes]).update(
                        status=Employee_Change_Queue.StatusCode.ERROR,
                        error_message=f"HTTP {response.status_code}: {response.text}"
                    )
            except requests.RequestException as e:
                Employee_Change_Queue.objects.filter(id__in=[c.id for c in changes]).update(
                    status=Employee_Change_Queue.StatusCode.ERROR,
                    error_message=str(e)
                )
