from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def vehicle_form_view(request):
    if request.method == "POST":
        code = request.POST.get("code")
        username = request.POST["username"]
        password = request.POST["password"]
        # if User.objects.filter(username=username).exists():
        #     return render(request, "vehicle_form/vehicle_form.html", {
        #         "error": "Errorooorroo."
        #     })
        # user = User.objects.create_user(username=username, password=password)
        # user.is_active = False
        # user.save()
        return render(request, "frontend/vehicle_form_done.html")

    sides = ["Front", "Driver's Side", "Rear", "Passenger Side"]
    return render(request, "frontend/vehicle_form/vehicle_form.html", {"sides": sides})
