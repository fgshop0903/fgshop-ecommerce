from django.db import models
from django.core.validators import RegexValidator
from django.urls import reverse

class Supplier(models.Model):
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('INACTIVO', 'Inactivo'),
        ('EN_EVALUACION', 'En Evaluación'),
    ]
    TIPO_PROVEEDOR_CHOICES = [
        ('MAYORISTA', 'Mayorista'),
        ('FABRICANTE', 'Fabricante'),
        ('DISTRIBUIDOR', 'Distribuidor'),
        ('MINORISTA_ESPECIAL', 'Minorista Especializado'),
        ('OTRO', 'Otro'),
    ]

    nombre_empresa = models.CharField(max_length=150, verbose_name="Nombre de la Empresa/Proveedor")
    ruc_validator = RegexValidator(regex=r'^\d{11}$', message='El RUC debe tener 11 dígitos.')
    ruc = models.CharField(
        max_length=11,
        validators=[ruc_validator],
        unique=True,
        verbose_name="RUC"
    )
    nombre_contacto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombre del Contacto Principal")
    
    phone_validator = RegexValidator(regex=r'^\+?1?\d{7,15}$', message="El número de teléfono es inválido.")
    telefono_contacto = models.CharField(
        validators=[phone_validator],
        max_length=20,
        blank=True, null=True,
        verbose_name="Teléfono de Contacto"
    )
    correo_contacto = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico de Contacto")
    sitio_web = models.URLField(blank=True, null=True, verbose_name="Sitio Web")
    logo = models.ImageField(upload_to='suppliers/logos/', blank=True, null=True, verbose_name="Logo de la Empresa")

    direccion_fiscal = models.TextField(blank=True, null=True, verbose_name="Dirección Fiscal")
    direccion_almacen = models.TextField(blank=True, null=True, verbose_name="Dirección de Almacén/Recojo (si aplica)")
    
    tipo_proveedor = models.CharField(
        max_length=25,
        choices=TIPO_PROVEEDOR_CHOICES,
        blank=True, null=True,
        verbose_name="Tipo de Proveedor"
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='ACTIVO',
        verbose_name="Estado del Proveedor"
    )

    terminos_pago = models.CharField(max_length=100, blank=True, null=True, help_text="Ej: Contado, Crédito 30 días", verbose_name="Términos de Pago Acordados")
    tiempo_entrega_promedio_a_fg = models.CharField(max_length=50, blank=True, null=True, help_text="Ej: 2-3 días, 1 semana", verbose_name="Tiempo Promedio de Entrega (a FG Shop)")
    calificacion_interna = models.PositiveSmallIntegerField(
        blank=True, null=True,
        choices=[(i, str(i)) for i in range(1, 6)], # 1 a 5 estrellas
        verbose_name="Calificación Interna (1-5)"
    )
    observaciones_generales = models.TextField(blank=True, null=True, verbose_name="Observaciones Generales")

    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre_empresa']

    def __str__(self):
        return self.nombre_empresa

    def get_absolute_url(self):
        # Asume que tendrás una vista de detalle para proveedores
        return reverse('mysuppliers:supplier_detail', kwargs={'pk': self.pk})

    # Podrías añadir un @property para ver los productos asociados si implementas SupplierProduct
    # @property
    # def productos_ofrecidos(self):
    #     return self.supplierproduct_set.all()