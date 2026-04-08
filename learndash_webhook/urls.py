from django.urls import path
from .views import learndash_webhook

urlpatterns = [
    path("", learndash_webhook, name="learndash_webhook"),
]
