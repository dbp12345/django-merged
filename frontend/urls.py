from django.urls import path

from frontend.views.accounts import views
from frontend.views.main import main
from frontend.views.cabinet import cabinet
from frontend.views.resources import resources
from frontend.views.pwa import pwa
from frontend.views.vehicle_form import vehicle_form
from frontend.views.docs import docs

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("", main.main_view, name="main"),
    path("cabinet/", cabinet.cabinet_view, name="cabinet"),
    path("pwa/", pwa.pwa_view, name="pwa"),
    path("resources/", resources.resources_view, name="resources"),
    path("resources/vehicle_form/", vehicle_form.vehicle_form_view, name="vehicle_form"),
    path("docs/<str:slug>/", docs.docs_view, name="front_documentation"),
]
