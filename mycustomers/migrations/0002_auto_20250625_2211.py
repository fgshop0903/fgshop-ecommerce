# mycustomers/migrations/0002_createsuperuser.py (o el nombre que se haya generado)

from django.db import migrations
import os

def create_superuser(apps, schema_editor):
    """Crea un superusuario usando variables de entorno."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

    if username and email and password:
        # Comprueba si el superusuario ya existe
        if not User.objects.filter(username=username).exists():
            print(f"Creando cuenta para el superusuario: {username}")
            User.objects.create_superuser(username=username, email=email, password=password)
        else:
            print(f"El superusuario {username} ya existe. Saltando creación.")
    else:
        print("Variables de entorno para superusuario no encontradas. Saltando creación.")


class Migration(migrations.Migration):

    dependencies = [
        ('mycustomers', '0001_initial'), # Asegúrate que dependa de la última migración de tu app
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]