from django.urls import path
from . import pwa_views

app_name = "contacts_pwa"

urlpatterns = [
    path("", pwa_views.pwa_checkin_page, name="pwa1_checkin_page"),
    path("api/checkin/<int:contact_id>/", pwa_views.api_checkin_contact, name="pwa1_api_checkin_contact"),
]
