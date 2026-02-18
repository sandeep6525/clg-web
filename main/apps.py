# main/apps.py
from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"
    verbose_name = "CS Department"

    def ready(self):
        # Place for signals import if you add a signals.py later
        # from . import signals  # noqa: F401
        pass
