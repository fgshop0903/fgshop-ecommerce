# mypurchases/models.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models import F, Sum
from decimal import Decimal # ¡Importamos Decimal para ser explícitos!

from mysuppliers.models import Supplier
from myproducts.models import ProductVariant

# =============================================================================
#  MODELO 1: LA ORDEN DE COMPRA (EL DOCUMENTO MAESTRO)
# =============================================================================
class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Borrador'
        SUBMITTED = 'SUBMITTED', 'Enviada al Proveedor'
        APPROVED = 'APPROVED', 'Aprobada'
        PARTIALLY_DELIVERED = 'PARTIALLY_DELIVERED', 'Entregada Parcialmente'
        FULLY_DELIVERED = 'FULLY_DELIVERED', 'Entregada Totalmente'
        CANCELLED = 'CANCELLED', 'Cancelada'

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        PARTIALLY_PAID = 'PARTIALLY_PAID', 'Pagada Parcialmente'
        FULLY_PAID = 'FULLY_PAID', 'Pagada Totalmente'
        OVERPAID = 'OVERPAID', 'Sobrepagada'

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders', verbose_name="Proveedor")
    order_date = models.DateField(verbose_name="Fecha de Orden")
    expected_delivery_date = models.DateField(blank=True, null=True, verbose_name="Fecha de Entrega Esperada")
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT, verbose_name="Estado de la Orden")
    invoice_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nº de Factura Proveedor")
    invoice_date = models.DateField(blank=True, null=True, verbose_name="Fecha de Factura")
    payment_due_date = models.DateField(blank=True, null=True, verbose_name="Fecha Vencimiento de Pago")
    
    # --- CORRECCIONES DE TIPO DE DATO ---
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Subtotal (Productos)")
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Costo de Envío")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Monto Total (incl. envío)")
    
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, verbose_name="Estado del Pago")
    document_file = models.FileField(upload_to='purchase_invoices/%Y/%m/', blank=True, null=True, verbose_name="Archivo de Factura/Guía")
    
    is_installment = models.BooleanField(default=False, verbose_name="¿Es compra a cuotas?")
    installments_count = models.PositiveIntegerField(default=0, verbose_name="Número de cuotas")
    
    # --- CORRECCIÓN DE TIPO DE DATO ---
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Monto por cuota")
    
    notes = models.TextField(blank=True, null=True, verbose_name="Notas / Observaciones")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_purchase_orders', verbose_name="Creado por")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"
        ordering = ['-order_date']

    def __str__(self):
        return f"OC-{self.id} a {self.supplier.nombre_empresa} ({self.order_date})"
    
    def calculate_totals(self):
        """
        Calcula el subtotal (suma de ítems) y el total (subtotal + envío).
        """
        # --- CORRECCIÓN DE TIPO DE DATO ---
        subtotal = self.items.aggregate(total=Sum(F('quantity') * F('unit_cost')))['total'] or Decimal('0.00')
        self.subtotal_amount = subtotal
        self.total_amount = self.subtotal_amount + (self.shipping_cost or Decimal('0.00'))
        self.save(update_fields=['subtotal_amount', 'total_amount'])

# =============================================================================
#  MODELO 2: LOS ÍTEMS DENTRO DE UNA ORDEN DE COMPRA
# =============================================================================
class PurchaseOrderItem(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente de Recepción'
        RECEIVED = 'RECEIVED', 'Recibido Completamente'

    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items', verbose_name="Orden de Compra")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name='purchase_items', verbose_name="Variante de Producto")
    quantity = models.PositiveIntegerField(verbose_name="Cantidad Pedida")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo por Unidad (sin IGV)")
    received_quantity = models.PositiveIntegerField(default=0, verbose_name="Cantidad Recibida")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name="Estado del Ítem")

    @property
    def subtotal(self):
        if self.quantity is None or self.unit_cost is None:
            # --- CORRECCIÓN DE TIPO DE DATO ---
            return Decimal('0.00')
        return self.quantity * self.unit_cost

    class Meta:
        verbose_name = "Ítem de Orden de Compra"
        verbose_name_plural = "Ítems de Órdenes de Compra"
        unique_together = ('purchase_order', 'variant')

    def __str__(self):
        return f"{self.quantity} x {self.variant.product.nombre} ({self.variant.nombre_variante})"
    
# =============================================================================
#  MODELO 3: REGISTRO DE CADA PAGO REALIZADO A UNA ORDEN
# =============================================================================
class PurchasePayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('TRANSFERENCIA_BCP', 'Transferencia BCP'),
        ('TRANSFERENCIA_INTERBANK', 'Transferencia Interbank'),
        ('YAPE', 'Yape'),
        ('PLIN', 'Plin'),
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA_CREDITO', 'Tarjeta de Crédito'),
        ('OTRO', 'Otro'),
    ]
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='payments', verbose_name="Orden de Compra")
    payment_date = models.DateField(verbose_name="Fecha de Pago")
    # --- CORRECCIÓN DE TIPO DE DATO ---
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name="Monto Pagado")
    payment_method = models.CharField(
        max_length=50, 
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name="Método de Pago"
    )
    reference_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="Código de Referencia/Operación")
    receipt_file = models.FileField(
        upload_to='purchase_payments/%Y/%m/', 
        blank=True, null=True, 
        verbose_name="Comprobante de Pago"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Pago de Compra"
        verbose_name_plural = "Pagos de Compras"
        ordering = ['-payment_date']

    def __str__(self):
        return f"Pago de S/ {self.amount} para OC-{self.purchase_order.id}"

# =============================================================================
#  MODELO 4 Y 5 (SIN CAMBIOS, YA ESTABAN BIEN)
# =============================================================================
class PurchaseDelivery(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='deliveries', verbose_name="Orden de Compra")
    delivery_date = models.DateField(verbose_name="Fecha de Entrega")
    tracking_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Número de Seguimiento")
    notes = models.TextField(blank=True, null=True, verbose_name="Notas de Entrega")
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Recibido por")

    class Meta:
        verbose_name = "Recepción de Mercadería"
        verbose_name_plural = "Recepciones de Mercadería"
        ordering = ['-delivery_date']

    def __str__(self):
        return f"Entrega para OC-{self.purchase_order.id} el {self.delivery_date}"

class PurchaseDeliveryItem(models.Model):
    delivery = models.ForeignKey(PurchaseDelivery, on_delete=models.CASCADE, related_name='items', verbose_name="Recepción")
    order_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.CASCADE, related_name='delivery_items', verbose_name="Ítem de la Orden")
    quantity_received = models.PositiveIntegerField(verbose_name="Cantidad Recibida en esta entrega")

    class Meta:
        verbose_name = "Ítem Recibido"
        verbose_name_plural = "Ítems Recibidos"

    def __str__(self):
        return f"{self.quantity_received} x {self.order_item.variant.nombre_variante} recibidos"