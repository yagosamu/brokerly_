from django.apps import AppConfig


class CommissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'commissions'

    def ready(self):
        from commissions import signals  # noqa: F401
