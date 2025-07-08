# core/views.py

from django.shortcuts import render
from myproducts.models import Product, Categoria, ProductVariant, AttributeImage
from django.db.models import Prefetch, Min, Q
from collections import defaultdict
from .models import Banner, Testimonial

def home_view(request):
    # Obtener IDs de productos nuevos y en oferta (esto está bien)
    new_product_ids = list(Product.objects.filter(activo=True).order_by('-creado').values_list('id', flat=True)[:80])
    sale_product_ids = list(Product.objects.filter(activo=True, destacado=True).order_by('?').values_list('id', flat=True)[:15])
    all_product_ids = list(set(new_product_ids + sale_product_ids))

    # --- ¡AQUÍ ESTÁ LA CORRECCIÓN CLAVE! ---
    # COPIAMOS LA LÓGICA EXACTA Y OPTIMIZADA DEL MIXIN
    products_queryset = Product.objects.filter(id__in=all_product_ids).annotate(
        min_variant_price=Min('variants__precio_variante', filter=Q(variants__activo=True, variants__stock_disponible__gt=0))
    ).select_related(
        'brand', 'supplier', 'visual_attribute'
    ).prefetch_related(
        Prefetch(
            'variants',
            queryset=ProductVariant.objects.filter(activo=True).prefetch_related('options__attribute'),
            to_attr='active_variants'
        ),
        Prefetch(
            'attribute_images',
            queryset=AttributeImage.objects.select_related('attribute_value').order_by('orden_visualizacion'),
            to_attr='prefetched_images'
        )
    )

    # Mapeamos las imágenes que ya precargamos
    images_map = defaultdict(lambda: defaultdict(list))
    for product in products_queryset:
        if hasattr(product, 'prefetched_images'):
            for img in product.prefetched_images:
                images_map[product.id][img.attribute_value_id].append(img.image.url)

    # Bucle final para enriquecer cada producto
    product_map = {p.id: p for p in products_queryset}
    for pid, producto in product_map.items():
        visual_attribute_slug = producto.visual_attribute.slug if producto.visual_attribute else 'color'

        sorted_variants = sorted(getattr(producto, 'active_variants', []), key=lambda v: v.precio_variante)
        producto.variant_to_display = sorted_variants[0] if sorted_variants else None
        
        producto.main_image_url = ''
        if producto.variant_to_display:
            visual_option = next((opt for opt in producto.variant_to_display.options.all() if opt.attribute.slug == visual_attribute_slug), None)
            if visual_option and images_map[pid].get(visual_option.id):
                producto.main_image_url = images_map[pid][visual_option.id][0]

        if not producto.main_image_url and hasattr(producto, 'prefetched_images') and producto.prefetched_images:
            producto.main_image_url = producto.prefetched_images[0].image.url
        
        # ¡IMPORTANTE! Usamos 'visual_options' para ser consistentes con el Mixin
        producto.visual_options = []
        unique_visuals = set()
        if hasattr(producto, 'active_variants'):
            for variant in producto.active_variants:
                for option in variant.options.all():
                    if option.attribute.slug == visual_attribute_slug and option.value not in unique_visuals:
                        unique_visuals.add(option.value)
                        all_images = images_map.get(pid, {}).get(option.id, [])
                        if all_images:
                            producto.visual_options.append({
                                'name': option.value,
                                'code': option.color_code,
                                'images': all_images
                            })
    # --- FIN DE LA CORRECCIÓN ---

    # Separar los productos para el contexto (usando el mapa enriquecido)
    new_products = [product_map[pid] for pid in new_product_ids if pid in product_map]
    sale_products = [product_map[pid] for pid in sale_product_ids if pid in product_map]
    
    # El resto de tu vista está perfecta
    featured_categories = Categoria.objects.filter(padre__isnull=True, imagen_categoria__isnull=False).order_by('?')[:25]
    banners = Banner.objects.filter(activo=True).order_by('orden', '-id')
    dynamic_testimonials = Testimonial.objects.filter(is_active=True).order_by('order')

    context = {
        'featured_categories': featured_categories,
        'new_products': new_products,
        'sale_products': sale_products,
        'banners': banners,
        'dynamic_testimonials': dynamic_testimonials, 
    }
    
    return render(request, 'core/home.html', context)