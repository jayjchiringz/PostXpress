from django.apps import AppConfig


class PostalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'postal'

    def ready(self):
        # Import the signals here
        from . import models

