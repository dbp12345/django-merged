from django.urls import path

from pwa_notifications.views.main import notifications_view, send_notification_view
from pwa_notifications.views.accounts import views

urlpatterns = [
    path("", notifications_view, name="notifications_index"),
    path("login/", views.login_view, name="notifications_login"),
    path("logout/", views.logout_view, name="notifications_logout"),
    path("send/", send_notification_view, name="notifications_send"),
]
