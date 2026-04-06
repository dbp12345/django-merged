from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django import forms
from django.contrib.auth import authenticate
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect


class PWAAuthForm(forms.Form):
    username = forms.CharField(label="Username", max_length=150)
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)

    error_messages = {
        "invalid_login": _("Incorrect username or password."),
        "inactive": _("The account has been disabled."),
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get("username")
        password = cleaned.get("password")
        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(self.error_messages["invalid_login"], code="invalid_login")
            if not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages["inactive"], code="inactive")
        return cleaned

    def get_user(self):
        return self.user_cache


@csrf_protect
def login_view(request):
    next_url = request.GET.get("next") or request.POST.get("next") or reverse("notifications_index")
    if request.method == "POST":
        form = PWAAuthForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(next_url)
    else:
        form = PWAAuthForm(request=request)
    return render(request, "notifications/accounts/login.html", {"form": form, "next": next_url})


def logout_view(request):
    logout(request)
    return redirect("notifications_login")

