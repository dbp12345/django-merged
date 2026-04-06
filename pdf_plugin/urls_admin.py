from django.urls import path
from .admin_views import render_pdf_admin

urlpatterns = [
    path(
        "render/<slug:template_name>/<str:pk>/",
        render_pdf_admin,
        name="pdf_plugin_render_admin",
    ),
]
