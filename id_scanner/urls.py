from django.urls import path

from . import views

app_name = "id_scanner"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("scan/", views.scan_submit, name="scan_submit"),
]
