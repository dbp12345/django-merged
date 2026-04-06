import json
from django.shortcuts import render

from company.models import Employees
from dispatch.models.Dispatch import Truck
from dispatch.models.VehicleCheckout import VehicleCheckout
from frontend.forms import VehicleCheckoutForm
from pwa_vehicle.decorators import employee_required


@employee_required
def vehicle_form_view(request):
    form = VehicleCheckoutForm()
    employee = Employees.objects.get(id=request.session["employee_id"])

    trucks = Truck.objects.all()

    truck_statuses = {}
    for truck in trucks:
        last_checkout = (
            VehicleCheckout.objects
            .filter(truck=truck)
            .order_by("-created_at")
            .first()
        )
        if last_checkout:
            status = "Returning" if last_checkout.status == "Checkout" else "Checkout"
        else:
            status = "Checkout"
        truck_statuses[truck.id] = status

    try:
        if request.method == "POST":
            form = VehicleCheckoutForm(request.POST, request.FILES)
            if form.is_valid():
                checkout = form.save(commit=False)
                checkout.employee = employee
                checkout.save()
                return render(request, "pwa_vehicle/vehicle_form/vehicle_form_done.html", {"employee": employee})
    except Exception as e:
        return render(request, "pwa_vehicle/vehicle_form/vehicle_form.html", {
            "form": form,
            "employee": employee,
            "error": {"error": str(e)},
        })

    return render(request, "pwa_vehicle/vehicle_form/vehicle_form.html", {
        "form": form,
        "employee": employee,
        "truck_names": json.dumps([str(t) for t in trucks]),
        "truck_name_to_id": json.dumps({str(t): t.id for t in trucks}),
        "truck_id_to_plate": json.dumps({t.id: t.license_plate for t in trucks}),
        "truck_id_to_status": json.dumps(truck_statuses),
        "license_plates": json.dumps([
            t.license_plate for t in trucks if t.license_plate
        ]),
    })
