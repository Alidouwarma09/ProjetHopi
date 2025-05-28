from django.apps import AppConfig


class ModelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Model'

    def ready(self):
        import Model.signals
