from django.urls import path

# from frontend.views.accounts import views
from pwa_vehicle.views.accounts import views
from pwa_vehicle.views.vehicle_form import vehicle_form

urlpatterns = [
    path("", views.login_view, name="pwa_vehicle_login"),
    path("login/", views.login_view, name="pwa_vehicle_login"),
    # path("register/", views.register_view,{"app_type": "pwa"}, name="pwa_vehicle_register"),
    path("logout/", views.logout_view,name="pwa_vehicle_logout"),
    path("vehicle_form/", vehicle_form.vehicle_form_view,name="pwa_vehicle_vehicle_form"),
]
