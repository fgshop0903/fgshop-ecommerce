from django.apps import AppConfig

class MycartConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mycart'
    verbose_name = "Carrito de Compras"

    def ready(self):
        # Importar las señales para que se registren
        import mycart.signals  