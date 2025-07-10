# core/views.py

from django.shortcuts import render
from myproducts.models import Product, Categoria, ProductVariant, AttributeImage
from django.db.models import Prefetch, Min, Q
from collections import defaultdict
from .models import Banner, Testimonial

def home_view(request):
    # 1. OBTENER IDs DE PRODUCTOS
    new_product_ids = list(Product.objects.filter(activo=True).order_by('-creado').values_list('id', flat=True)[:80])
    sale_product_ids = list(Product.objects.filter(activo=True, destacado=True).order_by('?').values_list('id', flat=True)[:15])
    all_product_ids = list(set(new_product_ids + sale_product_ids))

    # 2. OPTIMIZAR LA CONSULTA
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
            queryset=AttributeImage.objects.select_related(
                'attribute_value__attribute', 
                'variant__product__visual_attribute'
            ).prefetch_related('variant__options__attribute'),
            to_attr='prefetched_images'
        )
    )

    # 3. ENRIQUECER CADA PRODUCTO
    for producto in products_queryset:
        # Asignar la imagen principal
        producto.main_image_url = ''
        if hasattr(producto, 'prefetched_images') and producto.prefetched_images:
            producto.main_image_url = producto.prefetched_images[0].image.url

        # Asignar la variante por defecto para la tarjeta
        sorted_variants = sorted(getattr(producto, 'active_variants', []), key=lambda v: v.precio_variante)
        producto.variant_to_display = sorted_variants[0] if sorted_variants else None

        # Construir los swatches
        producto.visual_options = []
        unique_visuals = set()
        if hasattr(producto, 'prefetched_images'):
            for img in producto.prefetched_images:
                visual_option = img.visual_attribute_value
                if visual_option and visual_option.value not in unique_visuals:
                    unique_visuals.add(visual_option.value)
                    all_images_for_option = [
                        i.image.url for i in producto.prefetched_images 
                        if i.visual_attribute_value and i.visual_attribute_value.id == visual_option.id
                    ]
                    producto.visual_options.append({
                        'name': visual_option.value,
                        'code': visual_option.color_code,
                        'images': all_images_for_option
                    })

    # 4. PREPARAR EL CONTEXTO FINAL
    product_map = {p.id: p for p in products_queryset}
    new_products = [product_map[pid] for pid in new_product_ids if pid in product_map]
    sale_products = [product_map[pid] for pid in sale_product_ids if pid in product_map]
    
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