from django.apps import AppConfig

class MyordersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myorders'

    # --- INICIO DE LA MODIFICACIÓN ---
    def ready(self):
        """
        Este método se ejecuta cuando Django carga la aplicación.
        Es el lugar perfecto para importar y registrar nuestras señales.
        """
        import myorders.signals  # Importa el archivo de señales que acabamos de crear
    # --- FIN DE LA MODIFICACIÓN ---