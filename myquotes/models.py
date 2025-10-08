# myquotes/models.py

import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from myproducts.models import ProductVariant

class Quote(models.Model):
    class QuoteStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Borrador'
        SENT = 'SENT', 'Enviada'
        ACCEPTED = 'ACCEPTED', 'Aceptada'
        REJECTED = 'REJECTED', 'Rechazada'
        EXPIRED = 'EXPIRED', 'Expirada'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Datos del cliente (empresa)
    razon_social = models.CharField(max_length=255, verbose_name="Razón Social")
    ruc = models.CharField(max_length=11, verbose_name="RUC")
    direccion_cliente = models.TextField(verbose_name="Dirección", blank=True, null=True)
    atencion_a = models.CharField(max_length=255, blank=True, verbose_name="Atención a")
    email_cliente = models.EmailField(blank=True, verbose_name="Email de Contacto")
    telefono_cliente = models.CharField(max_length=20, blank=True, verbose_name="Teléfono de Contacto")
    
    # Información de la cotización
    numero_cotizacion = models.CharField(max_length=20, unique=True, editable=False, verbose_name="Nº Cotización")
    fecha_emision = models.DateField(auto_now_add=True, verbose_name="Fecha de Emisión")
    fecha_validez = models.DateField(verbose_name="Válida hasta")
    estado = models.CharField(max_length=10, choices=QuoteStatus.choices, default=QuoteStatus.DRAFT, verbose_name="Estado")
    
    # Campos para el PDF
    terminos_y_condiciones = models.TextField(blank=True, verbose_name="Términos y Condiciones", default="Garantía: 12 meses por defectos de fábrica. No incluye daños por mal uso.\nTiempo de entrega: 7-10 días hábiles una vez confirmada la compra.\nValidez de la oferta: Sujeta a la fecha indicada en el documento.")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones Adicionales")

    # Campos de totales (se calcularán automáticamente)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    igv = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='quotes_created')

    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-fecha_emision']

    def save(self, *args, **kwargs):
        if not self.numero_cotizacion:
            # Genera un número de cotización simple, ej: COT-0001
            last_quote = Quote.objects.order_by('id').last()
            new_id = (last_quote.pk and int(last_quote.numero_cotizacion.split('-')[1])) + 1 if last_quote else 1
            self.numero_cotizacion = f'COT-{new_id:04d}'
        super().save(*args, **kwargs)

    def calcular_totales(self):
        # El 18% de IGV en Perú
        IGV_RATE = Decimal('0.18')
        
        subtotal_calculado = sum(item.get_subtotal() for item in self.items.all())
        self.subtotal = subtotal_calculado
        self.igv = self.subtotal * IGV_RATE
        self.total = self.subtotal + self.igv
        self.save(update_fields=['subtotal', 'igv', 'total'])

    def __str__(self):
        return f"{self.numero_cotizacion} - {self.razon_social}"

class QuoteItem(models.Model):
    quote = models.ForeignKey(Quote, related_name='items', on_delete=models.CASCADE, verbose_name="Cotización")
    variant = models.ForeignKey(ProductVariant, related_name='quote_items', on_delete=models.SET_NULL, null=True, verbose_name="Producto (Variante)")
    descripcion = models.CharField(max_length=255, blank=True, help_text="Se autocompleta desde el producto, pero se puede editar.")
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Precio Unitario (Sin IGV)")

    class Meta:
        verbose_name = "Ítem de Cotización"
        verbose_name_plural = "Ítems de Cotización"

    def save(self, *args, **kwargs):
        if self.variant and not self.descripcion:
            self.descripcion = str(self.variant)
        super().save(*args, **kwargs)

    def get_subtotal(self):
        # Si la cantidad o el precio unitario aún no tienen valor, devuelve 0.
        if self.cantidad is None or self.precio_unitario is None:
            return Decimal('0.00')
        
        # Si ambos tienen valor, realiza la multiplicación.
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad} x {self.descripcion}"