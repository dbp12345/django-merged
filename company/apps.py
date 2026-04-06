from django.apps import AppConfig


class MyAppConfig(AppConfig):
    name = "company"

    def ready(self):
        # Import signals to register them
        from .signals import signals_for_parameters  # noqa: F401
        from .signals import signals_for_helpticket  # noqa: F401
