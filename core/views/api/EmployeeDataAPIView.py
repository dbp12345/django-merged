from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from rest_framework.permissions import BasePermission

from company.models import Employees
from company.services.EmployeesService import get_employee_parameters, update_employee_parameters_raw
from exchange.models import Contacts_Prop


class TokenAuthPermission(BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get("Authorization")
        return token == f"Token {settings.EXTERNAL_API_TOKEN}"


class EmployeeDataAPIView(APIView):
    permission_classes = [TokenAuthPermission]

    def post(self, request, *args, **kwargs):
        employee = None
        data = request.data
        employee_id = data.get("employee_id")
        employee_email = data.get("employee_email")
        parameters = data.get("parameters")

        if not (employee_id or employee_email) or not isinstance(parameters, list):
            return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        if employee_email:
            employee = Employees.objects.filter(email=employee_email).first()
        elif employee_id:
            employee = Employees.objects.filter(id=employee_id).first()

        if request.user.is_authenticated:
            username = request.user.username
        else:
            username = "django"

        parameters_dict = {}
        for param in parameters:
            param_name = param.get("name")
            param_value = param.get("value")
            contacts_prop_obj = Contacts_Prop.objects.filter(property_name=param_name).first()
            if contacts_prop_obj:
                parameters_dict[contacts_prop_obj] = param_value


        update_employee_parameters_raw(employee=employee, parameters=parameters_dict, modified_name=username)

        return Response({"status": "ok"}, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        data = request.data
        employee_id = data.get("employee_id")
        employee_email = data.get("employee_email")
        parameters = data.get("parameters")

        employee = None
        if not (employee_id or employee_email) or not isinstance(parameters, list):
            return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        if employee_id:
            employee = Employees.objects.filter(id=employee_id).first()

        if employee_email:
            employees_qs = list(Employees.objects.filter(email=employee_email))
            if len(employees_qs) == 0:
                return Response({"error": "Employee with this email not found"}, status=status.HTTP_404_NOT_FOUND)
            if len(employees_qs) > 1:
                return Response({"error": "Multiple employees found with this email"}, status=status.HTTP_409_CONFLICT)
            employee = employees_qs[0]

        response = {
            "employee": {
                "employee_id": employee.id,
                "employee_email": employee.email
            }
        }
        if employee:
            response["parameters"] = get_employee_parameters(employee=employee, parameters=parameters)

        return Response(response, status=status.HTTP_200_OK)


"""
curl "http://127.0.0.1:8000/api/employees/" -H "Authorization: Token YGRIcbf_6RosT2kw-s" -H "Content-Type: application/json" -d "{\"employee_id\": 25973, \"parameters\": [{\"name\": \"job_title\", \"value\": \"CRWB2-test\"}, {\"name\": \"DOB\", \"value\": \"09/19/2019\"}]}"
curl -X GET "http://127.0.0.1:8000/api/employees/" -H "Authorization: Token YGRIcbf_6RosT2kw-s" -H "Content-Type: application/json" -d "{\"employee_id\": 25973, \"parameters\": [{\"name\": \"job_title\"}, {\"name\": \"DOB\"}]}"
"""
