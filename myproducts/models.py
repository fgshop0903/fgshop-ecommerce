# myproducts/models.py

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from mysuppliers.models import Supplier
import uuid # Necesario para la lógica de slug único


# --- SIN CAMBIOS EN ESTOS MODELOS ---
class Brand(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Marca")
    slug = models.SlugField(max_length=110, unique=True, blank=True, help_text="Versión amigable para URL, se genera automáticamente.")
    logo = models.ImageField(upload_to='brands/', blank=True, null=True, verbose_name="Logo de la Marca")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción de la Marca")

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('myproducts:product_list_by_brand', args=[self.slug])


class Categoria(models.Model):
    # Quitamos unique=True de los campos individuales
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110, blank=True)

    padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategorias', verbose_name="Categoría Padre")
    imagen_categoria = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Imagen de la Categoría")
    guia_tallas_pdf = models.FileField(upload_to='guides/sizes/', blank=True, null=True, verbose_name="Guía de Tallas (PDF)")
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        # Regla de oro: La combinación de (padre y nombre) Y (padre y slug) deben ser únicas.
        unique_together = (('padre', 'nombre'), ('padre', 'slug'))
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        # Genera un slug básico si no existe
        if not self.slug:
            self.slug = slugify(self.nombre)
        
        # Bucle para asegurar que el slug sea único DENTRO del mismo padre
        original_slug = self.slug
        counter = 1
        # Mientras exista una categoría con el mismo padre y mismo slug (y no sea yo mismo)...
        while Categoria.objects.filter(padre=self.padre, slug=self.slug).exclude(pk=self.pk).exists():
            # ...le añado un contador al slug
            self.slug = f'{original_slug}-{counter}'
            counter += 1
            
        super().save(*args, **kwargs)

    def __str__(self):
        # Tu método __str__ está perfecto
        ruta = [self.nombre]
        actual = self.padre
        while actual:
            ruta.append(actual.nombre)
            actual = actual.padre
        return ' > '.join(reversed(ruta))

    def get_absolute_url(self):
        """
        Construye la URL jerárquica completa para la categoría.
        Ej: /productos/categoria/ropa/ropa-de-hombre/polos/
        """
        # Creamos una lista para guardar los slugs, empezando por el mío
        slugs = [self.slug]
        
        # Empezamos a "escalar" hacia el padre
        ancestro = self.padre
        while ancestro:
            # Añadimos el slug del ancestro al inicio de la lista
            slugs.insert(0, ancestro.slug)
            # Pasamos al siguiente ancestro (el abuelo)
            ancestro = ancestro.padre
            
        # Unimos todos los slugs con una barra para formar la ruta
        # El resultado será algo como: "ropa/ropa-de-hombre/polos"
        full_path = '/'.join(slugs)
        
        # Usamos reverse para construir la URL final con la ruta completa
        return reverse('myproducts:product_list_by_category', args=[full_path])
    
    def get_descendant_ids(self):
        # Tu método está perfecto
        descendant_ids = {self.id}
        children = self.subcategorias.all()
        for child in children:
            descendant_ids.update(child.get_descendant_ids())
        return list(descendant_ids)

class Attribute(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text="Nombre del atributo (ej. Color, Talla)")
    slug = models.SlugField(max_length=110, unique=True, blank=True, help_text="Slug para uso interno o URLs")

    class Meta:
        verbose_name = "Atributo"
        verbose_name_plural = "Atributos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values', verbose_name="Atributo")
    value = models.CharField(max_length=100, help_text="Valor del atributo (ej. Rojo, S, Algodón)")
    color_code = models.CharField(
        max_length=7, 
        blank=True, 
        null=True, 
        help_text="Código de color hexadecimal (ej. #FF0000) si este atributo es un color."
    )

    class Meta:
        verbose_name = "Valor de Atributo"
        verbose_name_plural = "Valores de Atributos"
        ordering = ['attribute', 'value']
        unique_together = ('attribute', 'value') 

    def __str__(self):
        return f"{self.attribute.nombre}: {self.value}"

# --- ÚNICA DEFINICIÓN DE PRODUCT ---
class Product(models.Model):
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name="productos")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="products_marca", verbose_name="Marca")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='products_supplied', verbose_name="Proveedor")
    descripcion = models.TextField(blank=True)
    especificaciones = models.JSONField(null=True, blank=True, default=dict, verbose_name="Especificaciones Técnicas", help_text='Almacena las especificaciones del producto como un diccionario JSON. Ejemplo: {"Marca": "Nike", "Material": "Cuero"}')
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Precio base si el producto no tiene variantes o como referencia.")
    configurable_attributes = models.ManyToManyField(Attribute, blank=True, related_name='configurable_products', help_text="Atributos que se usarán para crear variantes de este producto (ej. Talla, Color).")
    default_variant = models.OneToOneField('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_for_product', help_text="Variante que se muestra/usa por defecto si existe.")
    visual_attribute = models.ForeignKey(
        'Attribute',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visual_for_products',
        verbose_name="Atributo Visual Principal",
        help_text="El atributo que controla las imágenes (ej. Color para ropa, Sabor para suplementos)."
    )
    acepta_cuotas = models.BooleanField(
        default=False,
        verbose_name="Acepta pago en cuotas",
        help_text="Marcar si este producto puede ser pagado en cuotas."
    )
    numero_de_cuotas = models.PositiveIntegerField(
        default=12,
        verbose_name="Número de cuotas",
        help_text="Número máximo de cuotas para este producto (ej. 3, 6, 12)."
    )
    activo = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto (Maestro)"
        verbose_name_plural = "Productos (Maestros)"
        ordering = ['-creado']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nombre)
            unique_id = str(uuid.uuid4()).split('-')[0] # ID corto y único
            temp_slug = f"{base_slug}-{unique_id}"
            while Product.objects.filter(slug=temp_slug).exists():
                unique_id = str(uuid.uuid4()).split('-')[0]
                temp_slug = f"{base_slug}-{unique_id}"
            self.slug = temp_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('myproducts:product_detail', args=[self.slug])
    
    @property
    def get_display_price(self):
        if self.default_variant and self.default_variant.precio_variante is not None:
            return self.default_variant.precio_variante
        return self.precio_base

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="Producto Maestro")
    sku = models.CharField(max_length=100, unique=True, blank=True, editable=False) # Editable=False es ideal para campos autogenerados
    nombre_variante = models.CharField(max_length=255, blank=True, help_text="Nombre descriptivo (ej. Rojo / M). Se autogenera.")
    options = models.ManyToManyField(AttributeValue, related_name='product_variants', verbose_name="Opciones de Atributo")
    precio_variante = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio específico de esta variante.")
    stock_disponible = models.PositiveIntegerField(default=0, help_text="Stock para esta variante específica.")
    activo = models.BooleanField(default=True, help_text="¿Está esta variante disponible?")
    
    costo_proveedor_estimado_variante = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Costo para esta variante.")
    tiempo_entrega_estimado_variante = models.CharField(max_length=100, blank=True, null=True, help_text="Tiempo de entrega para esta variante.")

    class Meta:
        verbose_name = "Variante de Producto"
        verbose_name_plural = "Variantes de Productos"
        unique_together = ('product', 'nombre_variante') # Evita nombres de variante duplicados para el mismo producto

    def __str__(self):
        if self.nombre_variante:
            return f"{self.product.nombre} - {self.nombre_variante}"
        # Fallback por si el nombre aún no se ha generado
        option_values = " / ".join([str(opt.value) for opt in self.options.all().order_by('attribute__nombre')])
        return f"{self.product.nombre} - {option_values or 'Variante base'}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_visual_image_url(self):
        """
        Obtiene la URL de la imagen principal basada en el atributo visual del producto.
        Este método está optimizado para funcionar con los datos precargados (prefetched) de las vistas.
        """
        # Si la vista no precargó los datos necesarios, no podemos hacer nada.
        if not hasattr(self.product, 'visual_attribute') or not hasattr(self.product, 'prefetched_images'):
            return None

        # 1. Determinar el slug del atributo que estamos buscando (ej. 'color', 'sabor')
        visual_slug = self.product.visual_attribute.slug if self.product.visual_attribute else 'color'

        # 2. Encontrar la opción de ESTA variante que corresponde a ese atributo
        visual_option = None
        # self.options.all() usa los datos precargados si la vista los proveyó
        for option in self.options.all(): 
            if option.attribute.slug == visual_slug:
                visual_option = option
                break
        
        # 3. Si encontramos la opción, buscar su imagen en la lista de imágenes precargadas
        if visual_option:
            # Iteramos sobre la lista de imágenes que la vista ya trajo de la BD
            for image in self.product.prefetched_images:
                if image.attribute_value_id == visual_option.id:
                    return image.image.url # ¡Éxito! La encontramos.

        # 4. Fallback: Si no se encontró una imagen específica, devolver la primera imagen del producto.
        if hasattr(self.product, 'prefetched_images') and self.product.prefetched_images:
            return self.product.prefetched_images[0].image.url

        return None

# --- CAMBIO 1: NUEVO MODELO PARA GESTIONAR IMÁGENES POR ATRIBUTO ---

# ===================
# LÓGICA DE STOCK Y ACTIVACIÓN AUTOMÁTICA
# ===================
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=ProductVariant)
def actualizar_estado_activo_variant_y_producto(sender, instance, **kwargs):
    # Variante: Si stock = 0, desactiva; si stock > 0, activa
    if instance.stock_disponible == 0 and instance.activo:
        instance.activo = False
        instance.save(update_fields=['activo'])
    elif instance.stock_disponible > 0 and not instance.activo:
        instance.activo = True
        instance.save(update_fields=['activo'])

    # Producto maestro: Si todas las variantes están inactivas o sin stock, desactiva el producto
    producto = instance.product
    variantes_activas = producto.variants.filter(activo=True, stock_disponible__gt=0)
    if not variantes_activas.exists() and producto.activo:
        producto.activo = False
        producto.save(update_fields=['activo'])
    elif variantes_activas.exists() and not producto.activo:
        producto.activo = True
        producto.save(update_fields=['activo'])

class AttributeImage(models.Model):
    """
    Asocia imágenes a un valor de atributo específico para un producto.
    Ej: Para el "Polo Tommy", asocia 5 imágenes al valor "Color: Negro".
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attribute_images', null=True, blank=True)
    attribute_value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE, related_name='images', help_text="Asocia imágenes a un valor (ej. 'Color: Negro')")
    image = models.ImageField(upload_to='attribute_images/%Y/%m/%d/')
    alt_text = models.CharField(max_length=255, blank=True)
    orden_visualizacion = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Imagen de Atributo (por Color)"
        verbose_name_plural = "Imágenes de Atributos (por Color)"
        ordering = ['orden_visualizacion']
        unique_together = ('product', 'attribute_value', 'image') # Evita duplicados

    def __str__(self):
        return f"Imagen para {self.product.nombre} - {self.attribute_value}"

class EspecificacionPlantilla(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text="Ej: 'Plantilla para Ropa', 'Plantilla para Celulares'")
    # Usamos un campo de texto para listar las claves, una por línea.
    claves = models.TextField(
        help_text="Lista de claves de especificación, una por línea. Ej: 'Material', 'País de origen', etc."
    )

    class Meta:
        verbose_name = "Plantilla de Especificaciones"
        verbose_name_plural = "Plantillas de Especificaciones"

    def __str__(self):
        return self.nombre

    def to_json_dict(self):
        """Convierte las claves de texto a un diccionario JSON con valores vacíos."""
        # Limpiamos las líneas, quitamos las vacías y creamos el diccionario
        keys_list = [key.strip() for key in self.claves.splitlines() if key.strip()]
        return {key: "" for key in keys_list}
    
