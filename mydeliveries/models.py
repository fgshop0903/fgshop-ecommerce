from django.db import models
from django.urls import reverse
from myorders.models import Order # Ya usas el Order mejorado
# from mysuppliers.models import Supplier # Podrías enlazar si un envío viene directo de un proveedor

# Podrías tener una lista de transportistas predefinidos o un modelo para ellos
TRANSPORTISTA_CHOICES = [
    ('OLVA', 'Olva Courier'),
    ('SHALOM', 'Shalom Empresarial'),
    ('URBANO', 'Urbano Express'),
    ('INTERNO_FG', 'Entrega Interna FG Shop'),
    ('PROVEEDOR_DIRECTO', 'Directo del Proveedor'),
    ('OTRO', 'Otro'),
]

class Delivery(models.Model):
    ESTADO_ENTREGA = [
        ('PROGRAMADO', 'Programado'), # Nuevo: Planificado pero aún no en proceso físico
        ('PENDIENTE_RECOJO', 'Pendiente de Recojo (por transportista)'),
        ('EN_TRANSITO_A_FG', 'En Tránsito (a FG Shop)'), # Específico si el proveedor te envía primero
        ('RECIBIDO_EN_FG', 'Recibido (en FG Shop)'), # Específico
        ('PREPARANDO_ENVIO_CLIENTE', 'Preparando Envío (a cliente)'),
        ('EN_RUTA_CLIENTE', 'En Ruta (a cliente)'),
        ('ENTREGADO', 'Entregado al Cliente'),
        ('ENTREGA_FALLIDA', 'Entrega Fallida'),
        ('REPROGRAMADO', 'Reprogramado'),
        ('DEVUELTO', 'Devuelto'),
    ]

    # Relación con el pedido
    # Mantenemos OneToOne por ahora, asumiendo un solo envío final por pedido.
    # Si un pedido puede tener múltiples envíos (ej. un ítem se envía antes que otro),
    # cambia esto a: order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='deliveries')
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='delivery_info', # Cambiado de 'entrega' para evitar colisión con nombre de app
        verbose_name="Pedido Asociado"
    )

    # Información del envío
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación del Envío")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    fecha_programada_envio = models.DateField(
        blank=True, null=True,
        verbose_name="Fecha Programada de Envío/Recojo"
    ) # Fecha en que se espera que salga de FG o del proveedor
    fecha_estimada_entrega_cliente = models.DateField(
        blank=True, null=True,
        verbose_name="Fecha Estimada de Entrega al Cliente"
    )
    fecha_entrega_real_cliente = models.DateField(
        blank=True, null=True,
        verbose_name="Fecha de Entrega Real al Cliente"
    )

    estado_entrega = models.CharField(
        max_length=30, # Aumentado para nombres más largos
        choices=ESTADO_ENTREGA,
        default='PROGRAMADO',
        verbose_name="Estado de la Entrega"
    )
    transportista = models.CharField(
        max_length=50,
        choices=TRANSPORTISTA_CHOICES,
        blank=True, null=True,
        verbose_name="Transportista/Empresa de Envío"
    )
    entregado_por_persona = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Persona/Repartidor (si aplica)"
    ) # Tu campo 'entregado_por'
    numero_seguimiento = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Número de Seguimiento (Tracking)"
    )
    url_seguimiento = models.URLField(blank=True, null=True, verbose_name="URL de Seguimiento")

    costo_real_envio = models.DecimalField(
        max_digits=10, decimal_places=2,
        blank=True, null=True,
        verbose_name="Costo Real del Envío (para FG Shop)"
    )
    observaciones_envio = models.TextField(blank=True, null=True, verbose_name="Observaciones del Envío")

    # Campos para gestionar la entrega desde el proveedor a FG Shop (si aplica)
    # proveedor_envio = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='envios_realizados')
    # tracking_proveedor_a_fg = models.CharField(max_length=100, blank=True, null=True)
    # fecha_envio_proveedor = models.DateField(blank=True, null=True)
    # fecha_recepcion_fg = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ['-fecha_creacion'] # Ordenar por creación del registro de envío
        verbose_name = "Gestión de Envío"
        verbose_name_plural = "Gestión de Envíos"

    def __str__(self):
        return f"Envío para Pedido #{self.order.id_display} - Estado: {self.get_estado_entrega_display()}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


    def get_absolute_url(self):
        # Para el admin o vistas de detalle internas
        return reverse('mydeliveries:delivery_detail', kwargs={'pk': self.pk})

    @property
    def cliente_nombre(self):
        return self.order.nombre_cliente or (self.order.user.get_full_name() if self.order.user else "N/A")