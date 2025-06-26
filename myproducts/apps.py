from django.apps import AppConfig

class MyproductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myproducts' # Asegúrate que coincida con el nombre de tu directorio de app
    verbose_name = "Gestión de Productos" # Nombre más amigable para el admin

    # def ready(self):
    #     import myproducts.signals # Si tuvieras signals