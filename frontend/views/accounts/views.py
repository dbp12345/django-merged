import os

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

SECRET_CODE = os.getenv("REGISTRATION_INVITE_CODE")

def login_view(request, app_type = None):
    if request.user.is_authenticated:
        if app_type == "pwa":
            return redirect("pwa_vehicle_vehicle_form")
        else:
            return redirect("main")

    if request.method == "POST":
        raw_input = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = None

        if raw_input and password:
            # Пытаемся как username
            user = authenticate(request, username=raw_input, password=password)

            if not user:
                # Если не получилось, и это валидный email — ищем по email
                try:
                    validate_email(raw_input)
                    user_obj = User.objects.get(email__iexact=raw_input)
                    if user_obj.email:
                        user = authenticate(request, username=user_obj.username, password=password)
                except (ValidationError, User.DoesNotExist):
                    pass

        if user:
            login(request, user)
            if app_type == "pwa":
                return redirect("pwa_vehicle_vehicle_form")
            else:
                return redirect("main")
        else:
            if app_type == "pwa":
                return render(request, "pwa_vehicle/accounts/login.html", {"error": "Invalid credentials"})
            else:
                return render(request, "frontend/accounts/login.html", {"error": "Invalid credentials"})

    if app_type == "pwa":
        return render(request, "pwa_vehicle/accounts/login.html")
    else:
        return render(request, "frontend/accounts/login.html")


def register_view(request, app_type = None):
    if request.user.is_authenticated:
        if app_type == "pwa":
            return redirect("pwa_vehicle_vehicle_form")
        else:
            return redirect("main")
    if request.method == "POST":
        code = request.POST.get("code")
        if code != SECRET_CODE:
            if app_type == "pwa":
                return render(request, "pwa_vehicle/accounts/register.html", {"error": "Invalid code"})
            else:
                return render(request, "frontend/accounts/register.html", {"error": "Invalid code"})
        username = request.POST["username"]
        password = request.POST["password"]
        if User.objects.filter(username=username).exists():
            if app_type == "pwa":
                return render(request, "pwa_vehicle/accounts/register.html", {
                    "error": "This username is already taken."
                })
            else:
                return render(request, "frontend/accounts/register.html", {
                    "error": "This username is already taken."
                })
        user = User.objects.create_user(username=username, password=password)
        user.is_active = False
        user.save()
        if app_type == "pwa":
            return render(request, "pwa_vehicle/accounts/register_done.html")
        else:
            return render(request, "frontend/accounts/register_done.html")
            # login(request, user)
            # return redirect("main")

    if app_type == "pwa":
        return render(request, "pwa_vehicle/accounts/register.html")
    else:
        return render(request, "frontend/accounts/register.html")


def logout_view(request, app_type = None):
    logout(request)
    if app_type == "pwa":
        return redirect("pwa_vehicle_login")
    else:
        return redirect("login")
