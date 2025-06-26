from django.db import models

class Banner(models.Model):
    titulo = models.CharField(max_length=200, help_text="Título principal del banner")
    subtitulo = models.CharField(max_length=300, blank=True, help_text="Subtítulo o descripción breve")
    imagen = models.ImageField(upload_to='banners/', help_text="Imagen principal del banner para escritorio (Desktop). Dimensiones recomendadas: Ancho: 1920px - 2560px, Alto: 450px - 600px.")
    imagen_movil = models.ImageField(upload_to='banners/mobile/', blank=True, help_text="Imagen optimizada para dispositivos móviles (smartphones y tablets pequeñas). Dimensiones recomendadas: Ancho: 768px - 1024px, Alto: 300px - 450px. Considera que el contenido principal debe estar centrado.") # Nueva imagen para móvil
    url_destino = models.URLField(max_length=200, blank=True, help_text="URL a la que se redirigirá al hacer clic en el banner")
    texto_boton = models.CharField(max_length=50, blank=True, help_text="Texto que aparecerá en el botón (ej: 'Ver Ofertas')")
    activo = models.BooleanField(default=True, help_text="Marcar para que este banner se muestre en el carrusel")
    orden = models.PositiveIntegerField(default=0, help_text="Define el orden de aparición en el carrusel (menor número = primero)")

    class Meta:
        ordering = ['orden', '-id'] # Ordena por orden y luego por ID (para consistencia si varios tienen el mismo orden)
        verbose_name = "Banner del Carrusel"
        verbose_name_plural = "Banners del Carrusel"

    def __str__(self):
        return self.titulo
    
# core/models.py



class Testimonial(models.Model):
    author_name = models.CharField(max_length=100, verbose_name="Nombre del Cliente")
    testimonial_text = models.TextField(verbose_name="Testimonio")
    author_image = models.ImageField(upload_to='testimonials/authors/', blank=True, null=True, verbose_name="Imagen del Cliente")
    product_image = models.ImageField(upload_to='testimonials/products/', blank=True, null=True, verbose_name="Imagen del Producto") # ¡ASEGÚRATE QUE ESTÉ Y GUARDADO!
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden de visualización")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = "Testimonio"
        verbose_name_plural = "Testimonios"
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"Testimonio de {self.author_name} (Orden: {self.order})"

    @property
    def get_author_image_url(self):
        if self.author_image and hasattr(self.author_image, 'url'):
            return self.author_image.url
        return '/static/core/img/default_avatar.png'

    @property
    def get_product_image_url(self):
        if self.product_image and hasattr(self.product_image, 'url'):
            return self.product_image.url
        return '/static/core/img/default_product.png'