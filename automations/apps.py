from django.apps import AppConfig


class AutomationsConfig(AppConfig):
    """
    App configuration for automations app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "automations"
    verbose_name = "Automations"

    def ready(self):
        """
        Import signals when app is ready.
        This ensures signal handlers are registered.
        """
        import automations.signals  # noqa: F401
