import uuid # Para ID de pedido único y no secuencial
from django.db import models
from django.conf import settings # Para acceder a AUTH_USER_MODEL
from django.core.validators import MinValueValidator
from myproducts.models import Product
from myproducts.models import Product, ProductVariant

METODO_PAGO_CHOICES = [
    ('TRANSFERENCIA', 'Transferencia Bancaria'),
    ('EFECTIVO_CONTRAENTREGA', 'Efectivo Contraentrega (Limitado)'),
    ('PASARELA_ONLINE', 'Pasarela Online (Tarjeta/Yape/Plin)'),
    # Añade más según tus pasarelas
]

ESTADO_PEDIDO_CHOICES = [
    ('PENDIENTE_PAGO', 'Pendiente de Pago'),
    ('PAGO_CONFIRMADO', 'Pago Confirmado'), # Equivalente a tu "comprado"
    ('PROCESANDO_PROVEEDOR', 'Procesando con Proveedor'), # Específico a tu modelo
    ('EN_CAMINO_A_FGSHOP', 'En camino a FG Shop'), # Si primero llega a ti
    ('LISTO_PARA_ENVIO', 'Listo para Envío (Desde FG Shop)'),
    ('EN_CAMINO_CLIENTE', 'En Camino al Cliente'),
    ('ENTREGADO', 'Entregado'),
    ('CANCELADO', 'Cancelado'),
    ('REEMBOLSADO', 'Reembolsado'),
]

class Order(models.Model):
    # Identificación del pedido
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # ID único no secuencial
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Si se borra el user, el pedido queda pero sin user asociado
        null=True, blank=True, # Permite pedidos de "invitados" si lo implementas
        related_name='orders',
        verbose_name="Cliente"
    )
    # También podrías guardar una "copia" de los datos del cliente en el momento del pedido
    # por si el perfil del cliente cambia después.
    email_cliente = models.EmailField(blank=True, help_text="Correo del cliente al momento del pedido.")
    nombre_cliente = models.CharField(max_length=200, blank=True, help_text="Nombre del cliente al momento del pedido.")
    dni_cliente = models.CharField(max_length=20, blank=True, help_text="DNI/Documento del cliente al momento del pedido.")

    # Información de envío
    direccion_envio = models.TextField(verbose_name="Dirección de Envío")
    ciudad_envio = models.CharField(max_length=100, verbose_name="Ciudad de Envío")
    departamento_envio = models.CharField(max_length=100, verbose_name="Departamento de Envío")
    pais_envio = models.CharField(max_length=100, default="Perú", verbose_name="País de Envío")
    telefono_contacto_envio = models.CharField(max_length=20, blank=True, verbose_name="Teléfono de Contacto (Envío)")

    # Información de facturación (si es diferente al envío)
    usar_misma_direccion_facturacion = models.BooleanField(default=True)
    direccion_facturacion = models.TextField(blank=True, null=True, verbose_name="Dirección de Facturación")
    # ... más campos de facturación si son necesarios (RUC, Razón Social, etc.)

    # Detalles del pedido y pago
    fecha_pedido = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Pedido")
    actualizado = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    estado_pedido = models.CharField(
        max_length=30, # Aumentado para los nuevos estados
        choices=ESTADO_PEDIDO_CHOICES,
        default='PENDIENTE_PAGO',
        verbose_name="Estado del Pedido"
    )
    metodo_pago = models.CharField(
        max_length=30,
        choices=METODO_PAGO_CHOICES,
        blank=True, null=True, # Se establece cuando el pago se intenta/completa
        verbose_name="Método de Pago"
    )
    # Campos para el total, se calcularán a partir de los OrderItem
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Subtotal")
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Costo de Envío")
    # impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Si aplicas IGV u otros
    total_pedido = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Total del Pedido")

    # Información para tu modelo de negocio (dropshipping/bajo pedido)
    # El 'tiempo_entrega_estimado' ahora puede ser más dinámico o por item
    # origen_producto y observaciones pueden ir por OrderItem si varían por producto.
    # O mantenerlos aquí si es una nota general para todo el pedido.
    observaciones_internas = models.TextField(blank=True, null=True, help_text="Notas internas para FG Shop sobre este pedido.")
    observaciones_cliente = models.TextField(blank=True, null=True, help_text="Notas del cliente al realizar el pedido.")

    # Gestión
    pagado = models.BooleanField(default=False, verbose_name="¿Pagado?")
    id_transaccion_pago = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID Transacción de Pago")
    activo = models.BooleanField(default=True, help_text="Indica si el pedido es visible/activo en el sistema.") # Podrías usarlo para "archivar"

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_pedido']

    def __str__(self):
        return f"Pedido #{self.id_display} - {self.nombre_cliente or self.user.username if self.user else 'Invitado'}"

    @property
    def id_display(self):
        # Devuelve los primeros 8 caracteres del UUID para una visualización más corta
        return str(self.id)[:8].upper()

    def calcular_totales(self):
        """Calcula el subtotal y el total del pedido basado en sus items."""
        subtotal_calculado = sum(item.get_costo_total() for item in self.items.all())
        self.subtotal = subtotal_calculado
        # Aquí puedes añadir lógica para calcular el costo_envio si no es fijo
        # self.costo_envio = ...
        self.total_pedido = self.subtotal + self.costo_envio # + self.impuestos
        self.save(update_fields=['subtotal', 'total_pedido']) # Guardar solo estos campos
        return self.total_pedido

    def save(self, *args, **kwargs):
        if not self.email_cliente and self.user:
            self.email_cliente = self.user.email
        if not self.nombre_cliente and self.user:
            self.nombre_cliente = self.user.get_full_name() or self.user.username
        # Copiar DNI si el usuario tiene perfil y está disponible
        if not self.dni_cliente and self.user and hasattr(self.user, 'customerprofile'):
            self.dni_cliente = self.user.customerprofile.DNI or ''
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Pedido")
    variant = models.ForeignKey(
        ProductVariant, 
        related_name='order_items', 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name="Variante de Producto"
    )
    
    # --- CAMPOS DE "SNAPSHOT" (COPIA DE DATOS) ---
    nombre_producto = models.CharField(max_length=250, blank=True, verbose_name="Nombre Completo (Variante)")
    
    # Este es el precio de la variante, el que paga el cliente
    precio_unitario_variante = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio de Venta (Variante)")
    
    # Este es el precio base del producto maestro, para referencia
    precio_base_producto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio Base (Referencial)")

    # Guardamos el proveedor aquí
    proveedor_producto = models.CharField(max_length=150, blank=True, verbose_name="Proveedor")
    
    # Este campo sí lo llena el usuario
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Cantidad")

    class Meta:
        verbose_name = "Ítem de Pedido"
        verbose_name_plural = "Ítems de Pedidos"

    def __str__(self):
        return f"{self.cantidad} x {self.nombre_producto or 'Variante no disponible'}"

    def save(self, *args, **kwargs):
        # Lógica de auto-relleno al guardar (si el JS fallara, esto es un respaldo)
        if self.variant: 
            self.nombre_producto = str(self.variant)
            self.precio_unitario_variante = self.variant.precio_variante
            self.precio_base_producto = self.variant.product.precio_base
            if self.variant.product.supplier:
                self.proveedor_producto = self.variant.product.supplier.nombre_empresa
        super().save(*args, **kwargs)
        self.order.calcular_totales()

    def get_costo_total(self):
        # El costo total se calcula sobre el precio de la variante
        if self.precio_unitario_variante is None or self.cantidad is None:
            return 0.00
        return self.precio_unitario_variante * self.cantidad