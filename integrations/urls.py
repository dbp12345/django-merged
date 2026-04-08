from django.urls import path
from . import views

urlpatterns = [
    path("oauth/start/", views.ghl_oauth_start, name="ghl_oauth_start"),
    path("oauth/callback/", views.ghl_oauth_callback, name="ghl_oauth_callback"),
]
