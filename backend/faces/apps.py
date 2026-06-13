from django.apps import AppConfig


class FacesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "faces"

    def ready(self) -> None:
        # Register the Celery worker warm-load signal + HEIC opener.
        from . import engine  # noqa: F401
