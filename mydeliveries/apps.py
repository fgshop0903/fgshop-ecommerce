from django.apps import AppConfig

class MydeliveriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mydeliveries'

    def ready(self):
        """
        Este método es el lugar perfecto para importar y registrar nuestras señales.
        """
        import mydeliveries.signals # <-- AÑADE ESTA LÍNEA