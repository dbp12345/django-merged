from django.urls import path
from . import pwa_views

urlpatterns = [
    path("pwa/checkin/", pwa_views.pwa_checkin_page, name="pwa_checkin_page"),
    path("api/checkin/<int:contact_id>/", pwa_views.api_checkin_contact, name="api_checkin_contact"),
]
