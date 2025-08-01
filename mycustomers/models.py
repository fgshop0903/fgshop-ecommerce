from django.db import models
from django.contrib.auth.models import User # Importar el modelo User de Django
from django.core.validators import RegexValidator
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import random

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customerprofile')
    # 'nombre' y 'correo' ahora vienen de User (user.first_name, user.last_name, user.email)

    dni_validator = RegexValidator(regex=r'^\d{8}$', message='El DNI debe tener 8 dígitos.')
    DNI = models.CharField(
        max_length=8,
        validators=[dni_validator],
        unique=True, # DNI debe ser único
        null=True,
        blank=True, # Puede que un usuario se registre sin DNI inicialmente
        verbose_name="DNI"
    )
    # Podrías añadir un campo tipo_documento si manejas más de DNI (RUC, C.E., etc.)
    # TIPO_DOCUMENTO_CHOICES = [('DNI', 'DNI'), ('RUC', 'RUC'), ('CE', 'Carnet de Extranjería')]
    # tipo_documento = models.CharField(max_length=3, choices=TIPO_DOCUMENTO_CHOICES, default='DNI')


    # Validador para teléfono (ejemplo básico, se puede mejorar)
    phone_validator = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="El número de teléfono debe tener entre 9 y 15 dígitos, ej: +51987654321 o 987654321.")
    telefono = models.CharField(
        validators=[phone_validator],
        max_length=20,
        unique=True, # Teléfono también debería ser único
        null=True,
        blank=True,
        verbose_name="Teléfono"
    )
    direccion = models.TextField(blank=True, verbose_name="Dirección Principal")
    # 'activo' ahora se maneja con user.is_active
    # 'creado' y 'actualizado' pueden ser útiles aquí o usar los del User
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class TitleChoices(models.TextChoices):
        PATRONA = 'PA', _('Patrona')
        KING = 'KI', _('mi King')

    title_preference = models.CharField(
        _("Preferencia de Título"),
        max_length=2,
        choices=TitleChoices.choices,
        blank=True, # Lo hacemos opcional por si un usuario antiguo no lo tiene
        null=True,
        default=None
    )

    class Meta:
        verbose_name = "Perfil de Cliente"
        verbose_name_plural = "Perfiles de Clientes"
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"Perfil de {self.user.username} ({self.user.get_full_name() or self.user.email})"
    
    def get_title(self):
        """ Devuelve el título correcto, con variación para King/Rey. """
        if self.title_preference == self.TitleChoices.PATRONA:
            return "Patrona"
        if self.title_preference == self.TitleChoices.KING:
            return random.choice(["mi King", "mi Rey"])
        return ""
    
    def get_absolute_url(self):
    # Apuntar a la vista de detalle que puede ver el staff
        return reverse('mycustomers:customer_detail_admin', kwargs={'username': self.user.username})

    @property
    def nombre_completo(self):
        return self.user.get_full_name() or self.user.username

    @property
    def correo_electronico(self):
        return self.user.email
    
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name="Usuario")
    nombre_direccion = models.CharField(max_length=100, help_text="Ej: 'Casa', 'Oficina de Mamá'")
    
    # Podríamos tener campos separados o uno solo. Usemos separados para más flexibilidad.
    destinatario = models.CharField(max_length=200, verbose_name="Nombre del Destinatario")
    direccion = models.CharField(max_length=255, verbose_name="Dirección (Calle, número, etc.)")
    ciudad = models.CharField(max_length=100, verbose_name="Ciudad")
    departamento = models.CharField(max_length=100, verbose_name="Departamento / Región")
    pais = models.CharField(max_length=100, default="Perú")
    telefono_contacto = models.CharField(max_length=20, blank=True, verbose_name="Teléfono de Contacto")
    
    es_principal = models.BooleanField(default=False, verbose_name="¿Es dirección principal?")

    class Meta:
        verbose_name = "Dirección"
        verbose_name_plural = "Direcciones"
        ordering = ['-es_principal', 'nombre_direccion'] # Mostrar la principal primero

    def __str__(self):
        return f"Dirección '{self.nombre_direccion}' de {self.user.username}"