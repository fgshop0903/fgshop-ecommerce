from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import CustomerProfile

@receiver(post_save, sender=User)
def create_or_update_customer_profile(sender, instance, created, **kwargs):
    """
    Crea o actualiza el perfil del cliente cuando se crea o actualiza un User.
    """
    if created:
        CustomerProfile.objects.create(user=instance)
    # Guardar el perfil siempre que se guarde el User, puede ser redundante si no hay
    # campos en CustomerProfile que dependan directamente de cambios en User.
    # Pero es seguro para asegurar la consistencia.
    try:
        instance.customerprofile.save()
    except CustomerProfile.DoesNotExist:
        # Esto no debería pasar si 'created' se maneja bien, pero como fallback.
        CustomerProfile.objects.create(user=instance)