from django.contrib import admin
from .models import Banner, Testimonial

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'activo', 'orden', 'url_destino')
    list_editable = ('activo', 'orden')
    search_fields = ('titulo', 'subtitulo')
    list_filter = ('activo',)
    
@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'is_active', 'order', 'created_at')
    list_editable = ('is_active', 'order')
    search_fields = ('author_name', 'testimonial_text')
    list_filter = ('is_active',)
    ordering = ('order',)
    fields = ('author_name', 'testimonial_text', 'author_image', 'product_image', 'is_active', 'order') # Especifica los campos que quieres mostrar en el formulario