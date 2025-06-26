from django.apps import AppConfig

class MycustomersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mycustomers'
    verbose_name = "Gestión de Clientes y Usuarios"

    def ready(self):
        import mycustomers.signals # Importa las señales para que se registren