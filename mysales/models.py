# mysales/models.py

import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from myproducts.models import ProductVariant

METODO_PAGO_CHOICES = [
    ('TRANSFERENCIA_BCP', 'Transferencia BCP'),
    ('TRANSFERENCIA_INTERBANK', 'Transferencia Interbank'),
    ('YAPE', 'Yape'),
    ('PLIN', 'Plin'),
    ('EFECTIVO', 'Efectivo'),
    ('TARJETA_CREDITO', 'Tarjeta de Crédito'),
    ('OTRO', 'Otro'),
]

ESTADO_PEDIDO_CHOICES = [
    ('PENDIENTE_PAGO', 'Pendiente de Pago'),
    ('PAGO_CONFIRMADO', 'Pago Confirmado'),
    ('PROCESANDO_PROVEEDOR', 'Procesando con Proveedor'),
    ('EN_CAMINO_A_FGSHOP', 'En camino a FG Shop'),
    ('LISTO_PARA_ENVIO', 'Listo para Envío (Desde FG Shop)'),
    ('EN_CAMINO_CLIENTE', 'En Camino al Cliente'),
    ('ENTREGADO', 'Entregado'),
    ('CANCELADO', 'Cancelado'),
    ('REEMBOLSADO', 'Reembolsado'),
]

# =============================================================================
#  MODELO PARA VENTAS AL CONTADO
# =============================================================================
class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name="Cliente")
    email_cliente = models.EmailField(blank=True, help_text="Correo del cliente al momento del pedido.")
    nombre_cliente = models.CharField(max_length=200, blank=True, help_text="Nombre del cliente al momento del pedido.")
    dni_cliente = models.CharField(max_length=20, blank=True, help_text="DNI/Documento del cliente al momento del pedido.")
    direccion_envio = models.TextField(verbose_name="Dirección de Envío")
    ciudad_envio = models.CharField(max_length=100, verbose_name="Ciudad de Envío")
    departamento_envio = models.CharField(max_length=100, verbose_name="Departamento de Envío")
    pais_envio = models.CharField(max_length=100, default="Perú", verbose_name="País de Envío")
    telefono_contacto_envio = models.CharField(max_length=20, blank=True, verbose_name="Teléfono de Contacto (Envío)")
    usar_misma_direccion_facturacion = models.BooleanField(default=True)
    direccion_facturacion = models.TextField(blank=True, null=True, verbose_name="Dirección de Facturación")
    TIPO_COMPROBANTE_CHOICES = [
        ('BOLETA', 'Boleta de Venta'),
        ('FACTURA', 'Factura'),
    ]
    tipo_comprobante = models.CharField(
        max_length=10, 
        choices=TIPO_COMPROBANTE_CHOICES, 
        default='BOLETA',
        verbose_name="Tipo de Comprobante"
    )
    # Para Factura
    ruc = models.CharField(max_length=11, blank=True, null=True, verbose_name="RUC")
    razon_social = models.CharField(max_length=200, blank=True, null=True, verbose_name="Razón Social")
    direccion_fiscal = models.TextField(blank=True, null=True, verbose_name="Dirección Fiscal (Factura)")
    
    fecha_pedido = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Pedido")
    actualizado = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    estado_pedido = models.CharField(max_length=30, choices=ESTADO_PEDIDO_CHOICES, default='PENDIENTE_PAGO', verbose_name="Estado del Pedido")
    metodo_pago = models.CharField(max_length=30, choices=METODO_PAGO_CHOICES, blank=True, null=True, verbose_name="Método de Pago")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Subtotal")
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Costo de Envío")
    total_pedido = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Total del Pedido")
    observaciones_internas = models.TextField(blank=True, null=True, help_text="Notas internas para FG Shop sobre este pedido.")
    observaciones_cliente = models.TextField(blank=True, null=True, help_text="Notas del cliente al realizar el pedido.")
    pagado = models.BooleanField(default=False, verbose_name="¿Pagado?")
    id_transaccion_pago = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID Transacción de Pago")
    payment_receipt_file = models.FileField(upload_to='sales_receipts/%Y/%m/', blank=True, null=True, verbose_name="Archivo del Comprobante de Pago")
    activo = models.BooleanField(default=True, help_text="Indica si el pedido es visible/activo en el sistema.")

    class Meta:
        ordering = ['-fecha_pedido']
        verbose_name = "Orden de Venta (Contado)"
        verbose_name_plural = "Órdenes de Venta (Contado)"

    def __str__(self):
        return f"Pedido #{self.id_display} - {self.nombre_cliente or self.user.username if self.user else 'Invitado'}"

    @property
    def id_display(self):
        return str(self.id)[:8].upper()

    def calcular_totales(self):
        subtotal_calculado = sum(item.get_costo_total() for item in self.items.all())
        self.subtotal = subtotal_calculado
        self.total_pedido = self.subtotal + self.costo_envio
        self.save(update_fields=['subtotal', 'total_pedido'])
        return self.total_pedido

    def save(self, *args, **kwargs):
        if not self.email_cliente and self.user: self.email_cliente = self.user.email
        if not self.nombre_cliente and self.user: self.nombre_cliente = self.user.get_full_name() or self.user.username
        if not self.dni_cliente and self.user and hasattr(self.user, 'customerprofile'): self.dni_cliente = self.user.customerprofile.DNI or ''
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Pedido")
    variant = models.ForeignKey(ProductVariant, related_name='order_items', on_delete=models.SET_NULL, null=True, verbose_name="Variante de Producto")
    nombre_producto = models.CharField(max_length=250, blank=True, verbose_name="Nombre Completo (Variante)")
    precio_unitario_variante = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio de Venta (Variante)")
    precio_base_producto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio Base (Referencial)")
    proveedor_producto = models.CharField(max_length=150, blank=True, verbose_name="Proveedor")
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Cantidad")

    class Meta:
        verbose_name = "Ítem de Venta"
        verbose_name_plural = "Ítems de Venta"

    def __str__(self):
        return f"{self.cantidad} x {self.nombre_producto or 'Variante no disponible'}"

    def save(self, *args, **kwargs):
        if self.variant: 
            self.nombre_producto = str(self.variant)
            self.precio_unitario_variante = self.variant.precio_variante
            self.precio_base_producto = self.variant.product.precio_base
            if self.variant.product.supplier: self.proveedor_producto = self.variant.product.supplier.nombre_empresa
        super().save(*args, **kwargs)
        if self.order_id: self.order.calcular_totales()

    def get_costo_total(self):
        if self.precio_unitario_variante is None or self.cantidad is None:
            return Decimal('0.00')
        return self.precio_unitario_variante * self.cantidad

class SalePayment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', verbose_name="Orden de Venta")
    payment_date = models.DateField(verbose_name="Fecha de Pago")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Pagado")
    payment_method = models.CharField(max_length=50, blank=True, verbose_name="Método de Pago")
    reference_code = models.CharField(max_length=100, blank=True, verbose_name="Código de Referencia/Transacción")
    receipt_file = models.FileField(upload_to='sale_installments_receipts/%Y/%m/', blank=True, null=True, verbose_name="Comprobante de Cuota")
    notes = models.TextField(blank=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Pago de Venta"
        verbose_name_plural = "Pagos de Ventas"
        ordering = ['-payment_date']

    def __str__(self):
        return f"Pago de S/ {self.amount} para la Orden #{self.order.id_display}"

# =============================================================================
#  NUEVOS MODELOS PARA VENTAS A CRÉDITO / CUOTAS
# =============================================================================
class InstallmentSale(models.Model):
    class SaleStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Vigente'
        PAID_OFF = 'PAID_OFF', 'Pagado Completamente'
        LATE = 'LATE', 'En Atraso'
        CANCELLED = 'CANCELLED', 'Cancelado'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, # Si se borra el user, el crédito queda
        related_name='installment_sales', 
        verbose_name="Cliente (Opcional)",
        null=True, # Permite que este campo esté vacío
        blank=True # Lo hace no-requerido en los formularios
    )
    customer_name = models.CharField(max_length=200, verbose_name="Nombre del Cliente")
    customer_dni = models.CharField(max_length=20, blank=True, verbose_name="DNI del Cliente")
    customer_phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono del Cliente")
    customer_email = models.EmailField(blank=True, verbose_name="Email del Cliente")

    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, verbose_name="Variante Vendida")
    sale_date = models.DateField(verbose_name="Fecha del Acuerdo")
    fecha_primer_pago = models.DateField(
        verbose_name="Fecha de la Primera Cuota",
        null=True, 
        blank=True,
        help_text="Si se deja en blanco, la primera cuota será un mes después de la Fecha del Acuerdo."
    )
    product_cash_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Original al Contado")
    initial_payment = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Cuota Inicial")
    interest_rate = models.FloatField(default=0.0, verbose_name="Tasa de Interés (%)")
    number_of_installments = models.PositiveIntegerField(verbose_name="Número de Cuotas")
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto de cada Cuota")
    total_credit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Precio Total a Crédito (Calculado)")
    status = models.CharField(max_length=20, choices=SaleStatus.choices, default=SaleStatus.ACTIVE, verbose_name="Estado del Crédito")
    notes = models.TextField(blank=True, verbose_name="Notas del Acuerdo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        cash_price = Decimal(self.product_cash_price or '0.00')
        initial_payment = Decimal(self.initial_payment or '0.00')
        installments = self.number_of_installments or 1 
        principal = cash_price - initial_payment
        interest_rate_decimal = Decimal(self.interest_rate / 100.0)
        total_interest = principal * interest_rate_decimal * installments
        total_to_pay_in_installments = principal + total_interest
        if installments > 0:
            self.installment_amount = round(total_to_pay_in_installments / installments, 2)
        else:
            self.installment_amount = Decimal('0.00')
        self.total_credit_price = initial_payment + (self.installment_amount * installments)
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Venta a Cuotas"
        verbose_name_plural = "Ventas a Cuotas"
        ordering = ['-sale_date']

    def __str__(self):
        customer_identifier = self.customer_name or (self.user.username if self.user else 'Cliente no especificado')
        return f"Crédito para {self.variant} a {customer_identifier}"

class InstallmentPayment(models.Model):
    installment_sale = models.ForeignKey(InstallmentSale, on_delete=models.CASCADE, related_name='payments', verbose_name="Venta a Crédito")
    payment_date = models.DateField(verbose_name="Fecha de Pago")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Pagado")
    receipt_file = models.FileField(upload_to='installment_receipts/%Y/%m/', blank=True, null=True, verbose_name="Comprobante de Cuota")
    notes = models.TextField(blank=True, verbose_name="Notas del Pago")

    class Meta:
        verbose_name = "Pago de Cuota"
        verbose_name_plural = "Pagos de Cuotas"
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Pago de S/ {self.amount_paid} para crédito #{self.installment_sale.id}"