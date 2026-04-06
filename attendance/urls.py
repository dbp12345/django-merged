from django.urls import path

from attendance.views.punches_form import punches_form_view
from attendance.views.accounts import views

urlpatterns = [
    path("", punches_form_view,name="pwa_punches_form"),
    path("login/", views.login_view, name="pwa_attendance_login"),
    path("logout/", views.logout_view, name="pwa_attendance_logout"),
]
