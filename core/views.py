# core/views.py

from django.shortcuts import render
from myproducts.models import Product, Categoria, ProductVariant, AttributeValue, AttributeImage
from django.db.models import Prefetch, Min, Q
from collections import defaultdict
from .models import Banner, Testimonial 

def home_view(request):

    # Obtener IDs de productos nuevos y en oferta
    new_product_ids = list(Product.objects.filter(activo=True).order_by('-creado').values_list('id', flat=True)[:80])
    sale_product_ids = list(Product.objects.filter(activo=True, destacado=True).order_by('?').values_list('id', flat=True)[:15])
    all_product_ids = list(set(new_product_ids + sale_product_ids))

    # Hacemos un solo queryset para obtener todos los datos necesarios
    products_queryset = Product.objects.filter(id__in=all_product_ids).annotate(
        min_variant_price=Min('variants__precio_variante', filter=Q(variants__activo=True, variants__stock_disponible__gt=0))
    ).prefetch_related(
        Prefetch(
            'variants',
            queryset=ProductVariant.objects.filter(activo=True).prefetch_related('options__attribute'),
            to_attr='active_variants'
        ),
        'brand', 'supplier'
    )

    # Mapear imágenes para estos productos
    images_map = defaultdict(lambda: defaultdict(list))
    color_attribute_slug = 'color'
    attr_images = AttributeImage.objects.filter(
        product_id__in=all_product_ids,
        attribute_value__attribute__slug=color_attribute_slug
    ).select_related('attribute_value').order_by('orden_visualizacion')
    for img in attr_images:
        images_map[img.product_id][img.attribute_value.value].append(img.image.url)

    # Procesar y enriquecer cada producto
    product_map = {p.id: p for p in products_queryset}
    for pid, producto in product_map.items():
        sorted_variants = sorted(producto.active_variants, key=lambda v: v.precio_variante)
        producto.variant_to_display = sorted_variants[0] if sorted_variants else None
        
        producto.main_image_url = ''
        if producto.variant_to_display:
            color_val = next((opt.value for opt in producto.variant_to_display.options.all() if opt.attribute.slug == color_attribute_slug), None)
            if color_val and images_map[pid][color_val]:
                producto.main_image_url = images_map[pid][color_val][0]

        producto.color_info = []
        unique_colors = set()
        for variant in producto.active_variants:
            for option in variant.options.all():
                if option.attribute.slug == color_attribute_slug and option.value not in unique_colors:
                    unique_colors.add(option.value)
                    all_images = images_map.get(pid, {}).get(option.value, [])
                    if all_images:
                        producto.color_info.append({'name': option.value, 'code': option.color_code, 'images': all_images})
    
    # Separar los productos para el contexto
    new_products = [product_map[pid] for pid in new_product_ids if pid in product_map]
    sale_products = [product_map[pid] for pid in sale_product_ids if pid in product_map]
    
    # Categorías destacadas
    featured_categories = Categoria.objects.filter(padre__isnull=True, imagen_categoria__isnull=False).order_by('?')[:25]

    # ¡Aquí es donde añades los banners directamente al diccionario de contexto final!
    banners = Banner.objects.filter(activo=True).order_by('orden', '-id') # Ordena por 'orden' y luego por ID

    dynamic_testimonials = Testimonial.objects.filter(is_active=True).order_by('order')


    context = {
        'featured_categories': featured_categories,
        'new_products': new_products,
        'sale_products': sale_products,
        'banners': banners,
        'dynamic_testimonials': dynamic_testimonials, 
    }
    
    return render(request, 'core/home.html', context)