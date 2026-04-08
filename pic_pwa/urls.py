from django.urls import path
from . import views

urlpatterns = [
    path("", views.scan_qr, name="pic_scan"),
    path("<int:contact_id>/", views.take_photo, name="pic_take_photo"),
    path("<int:contact_id>/upload/", views.upload_photo, name="pic_upload_photo"),
]
