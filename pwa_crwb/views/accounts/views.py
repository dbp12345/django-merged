import os

from django.db.models import Q
from django.shortcuts import render, redirect

from company.models import Employees

SECRET_CODE = os.getenv("REGISTRATION_INVITE_CODE")


def login_view(request):
    if request.session.get("employee_id"):
        return redirect("pwa_crwb_crew")

    if request.method == "POST":
        raw_input = request.POST.get("raw_input", "").strip()
        if not raw_input:
            return redirect("pwa_vehicle_vehicle_form")

        try:
            emp = Employees.objects.get(
                Q(
                    Q(employees_parameters_entries__contacts_prop__property_name="email",
                      employees_parameters_entries__value=raw_input) |
                    Q(employees_parameters_entries__contacts_prop__property_name="MobilePhone",
                      employees_parameters_entries__value=raw_input)
                )
            )
            request.session["employee_id"] = emp.id
            return redirect("pwa_crwb_crew")
        except Employees.DoesNotExist:
            return render(request, "pwa_crwb/accounts/login.html", {"error": "Invalid credentials"})
        except Exception as e:
            import logging
            print("================ MY logging PWE login_view ================")
            print(str(e))
            logger = logging.getLogger("my_log")
            logger.error(
                "\n================ MY logging PWE login_view ================\n"
                f"Error        : {str(e)}\n"
            )
            return redirect("pwa_vehicle_vehicle_form")
            # return render(request, "pwa_vehicle/accounts/login.html", {"error": str(e)})

    return render(request, "pwa_crwb/accounts/login.html")


def logout_view(request):
    request.session.pop("employee_id", None)
    return redirect("pwa_crwb_login")
