from django.apps import AppConfig


class InsurersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'insurers'

    def ready(self):
        from insurers import signals  # noqa: F401
