# mypurchases/apps.py

from django.apps import AppConfig

class MypurchasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mypurchases'

    def ready(self):
        # Esta línea importa y conecta nuestras señales cuando la app está lista.
        import mypurchases.signals