from django.urls import path
from . import views

app_name = "checkin_pwa"

urlpatterns = [
    path("", views.checkin_page, name="index"),
    path("scan/", views.scan_checkin, name="scan"),
]
