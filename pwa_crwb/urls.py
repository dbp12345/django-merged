from django.urls import path

from core.views.cards.cards import CardsView
from pwa_crwb.views.accounts import views
from pwa_crwb.views.crwb_front.crew import crew_view
from pwa_crwb.views.crwb_front.dispatch import dispatch_view
from pwa_crwb.views.crwb_front.mspa import mspa_view

urlpatterns = [
    path("", views.login_view, name="pwa_crwb_login"),
    path("login/", views.login_view, name="pwa_crwb_login"),
    # path("register/", views.register_view,{"app_type": "pwa"}, name="pwa_crwb_register"),
    path("logout/", views.logout_view, name="pwa_crwb_logout"),
    path("dispatch/", dispatch_view, name="pwa_crwb_dispatch"),
    path("mspa/", mspa_view, name="pwa_crwb_mspa"),
    path("crew/", crew_view, name="pwa_crwb_crew"),
    path("card/", CardsView.as_view(), name="pwa_crwb_card"),
]
