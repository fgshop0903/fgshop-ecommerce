from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.http import Http404
from django.db.models import Q
import json
from .models import Product, Categoria, AttributeValue, Brand, Supplier
from .forms import ProductForm
from mycart.forms import CartAddProductForm
from django.core.serializers.json import DjangoJSONEncoder
from .models import ProductVariant
from mysuppliers.models import Supplier
from django.conf import settings
from .models import AttributeImage
from collections import defaultdict
from django.db.models import Prefetch, Min
from .models import Attribute
from mysuppliers.models import Supplier
from django.db.models import F
from .models import ProductVariant
from django.core.paginator import Paginator

from .models import (
    Product, Categoria, Brand, Supplier, 
    ProductVariant, AttributeImage, Attribute
)
from .forms import ProductForm

# =============================================================================
#  EL PAQUETE DE SUPERPODERES (NUESTRO MIXIN)
# =============================================================================
class ProductListOptimizationMixin:
    """
    Este Mixin se encarga de dos cosas:
    1. Optimizar la consulta de productos para evitar N+1 queries.
    2. Enriquecer cada producto con datos extra para las plantillas (imagen principal, swatches, etc).
    """
    context_object_name = 'productos'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.annotate(
            min_variant_price=Min('variants__precio_variante', filter=Q(variants__activo=True, variants__stock_disponible__gt=0))
        ).select_related(
            'brand', 'supplier', 'visual_attribute'
        ).prefetch_related(
            Prefetch(
                'variants',
                queryset=ProductVariant.objects.filter(activo=True).prefetch_related('options__attribute'),
                to_attr='active_variants'
            ),
            # ESTA ES LA PRECARGA COMPLETA Y CORRECTA
            Prefetch(
                'attribute_images',
                queryset=AttributeImage.objects.select_related(
                    'attribute_value__attribute', 
                    'variant__product__visual_attribute'
                ).prefetch_related('variant__options__attribute'),
                to_attr='prefetched_images'
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products_list = context.get(self.context_object_name, [])

        # Bucle para enriquecer cada producto
        for producto in products_list:
            # Asignar la imagen principal
            producto.main_image_url = ''
            if hasattr(producto, 'prefetched_images') and producto.prefetched_images:
                producto.main_image_url = producto.prefetched_images[0].image.url

            # --- ¡LA LÍNEA QUE FALTABA ESTÁ AQUÍ! ---
            # Asignar la variante por defecto para la tarjeta
            sorted_variants = sorted(getattr(producto, 'active_variants', []), key=lambda v: v.precio_variante)
            producto.variant_to_display = sorted_variants[0] if sorted_variants else None
            # --- FIN DE LA LÍNEA AÑADIDA ---

            # Construir los swatches usando la nueva propiedad inteligente del modelo
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
        return context

# =============================================================================
#  VISTAS CRUD (Crear, Editar, Borrar) - AHORA INCLUIDAS
# =============================================================================
class ProductCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'myproducts/product_form.html'
    success_message = "Producto '%(nombre)s' creado exitosamente."
    
    def get_success_url(self):
        return reverse_lazy('myproducts:product_detail', kwargs={'slug': self.object.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Registrar Nuevo Producto"
        context['nombre_boton'] = "Guardar Producto"
        return context

class ProductUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'myproducts/product_form.html'
    slug_url_kwarg = 'slug'
    success_message = "Producto '%(nombre)s' actualizado exitosamente."

    def get_success_url(self):
        return reverse_lazy('myproducts:product_detail', kwargs={'slug': self.object.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f"Editar Producto: {self.object.nombre}"
        context['nombre_boton'] = "Actualizar Producto"
        return context
    
class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'myproducts/product_confirm_delete.html'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('myproducts:product_list')

    def form_valid(self, form):
        messages.success(self.request, f"Producto '{self.object.nombre}' eliminado exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f"Eliminar Producto: {self.object.nombre}"
        return context

# =============================================================================
#  VISTAS DE LISTADO (Usando el Mixin)
# =============================================================================
class ProductListView(ProductListOptimizationMixin, ListView):
    model = Product
    template_name = 'myproducts/product_list.html'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset().filter(activo=True)
        self.categoria_actual = None
        category_path = self.kwargs.get('category_path')
        if category_path:
            slugs = category_path.split('/')
            parent = None
            for slug in slugs:
                self.categoria_actual = get_object_or_404(Categoria, slug=slug, padre=parent)
                parent = self.categoria_actual
        if self.categoria_actual:
            queryset = queryset.filter(categoria_id__in=self.categoria_actual.get_descendant_ids())
        return queryset.order_by('-destacado', '-creado')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categoria_actual'] = self.categoria_actual
        if self.categoria_actual:
            ruta_categoria = []
            cat_temp = self.categoria_actual
            while cat_temp:
                ruta_categoria.append(cat_temp)
                cat_temp = cat_temp.padre
            context['ruta_categoria'] = reversed(ruta_categoria)
        return context

class ProductSearchView(ProductListOptimizationMixin, ListView):
    model = Product
    template_name = 'myproducts/product_search_results.html'
    paginate_by = 16

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if not query:
            return Product.objects.none()
        
        search_results = Product.objects.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query) |
            Q(brand__nombre__icontains=query) | Q(categoria__nombre__icontains=query) |
            Q(variants__sku__icontains=query)
        ).filter(activo=True).distinct()
        
        # El super().get_queryset() ahora llama al Mixin
        return super().get_queryset().filter(pk__in=search_results.values_list('pk', flat=True))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        context['query'] = query
        context['search_performed'] = bool(query)
        context['titulo_pagina'] = f"Resultados para '{query}'" if query else "Búsqueda"
        return context

class ProductListByBrandView(ProductListOptimizationMixin, ListView):
    model = Product
    template_name = 'myproducts/product_list_by_brand.html'
    paginate_by = 12

    def get_queryset(self):
        self.brand = get_object_or_404(Brand, slug=self.kwargs['brand_slug'])
        return super().get_queryset().filter(brand=self.brand, activo=True).order_by('-creado')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_brand'] = self.brand
        context['page_title'] = f"Productos de la marca {self.brand.nombre}"
        return context

class ProductListBySupplierView(ProductListOptimizationMixin, ListView):
    model = Product
    template_name = 'myproducts/product_list_by_supplier.html'
    paginate_by = 12

    def get_queryset(self):
        self.supplier = get_object_or_404(Supplier, pk=self.kwargs['supplier_pk'])
        return super().get_queryset().filter(supplier=self.supplier, activo=True).order_by('-creado')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supplier'] = self.supplier
        context['page_title'] = f"Productos de {self.supplier.nombre_empresa}"
        return context

# =============================================================================
#  VISTA DE DETALLE
# =============================================================================
class ProductDetailView(DetailView):
    model = Product
    template_name = 'myproducts/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        variants_queryset = product.variants.filter(activo=True).prefetch_related('options__attribute')

        if not variants_queryset.exists():
            context['variants_data_json'] = {} # Enviar diccionario vacío
            return context

        attribute_images_map = defaultdict(list)
        image_query = AttributeImage.objects.filter(product=product).order_by('orden_visualizacion')
        for attr_img in image_query:
            attribute_images_map[attr_img.attribute_value_id].append(attr_img.image.url)

        variants_data = {
            'attributes_definition': [],
            'variants': [],
            'product_base_price': str(product.precio_base) if product.precio_base else None,
            'default_variant_id': None,
            'use_variant_specific_images': product.use_variant_specific_images
        }
        
        visual_attribute_slug = product.visual_attribute.slug if product.visual_attribute else 'color'
        
        for attribute in product.configurable_attributes.all().order_by('nombre'):
            options = sorted(list(variants_queryset.filter(options__attribute=attribute).values_list('options__value', flat=True).distinct()))
            if options:
                if attribute.slug == 'talla':
                    size_order = ['S', 'M', 'L', 'XL', '2XL', '3XL']
                    options.sort(key=lambda s: size_order.index(s) if s in size_order else float('inf'))
                
                variants_data['attributes_definition'].append({
                    'id_slug': attribute.slug,
                    'name': attribute.nombre,
                    'type': 'image_swatch' if attribute.slug == visual_attribute_slug else 'button',
                    'options_display_order': options
                })
        
        for variant in variants_queryset:
            variant_dict = {
                'id': variant.id, 'sku': variant.sku, 'price': str(variant.precio_variante),
                'stock': variant.stock_disponible, 'is_active': variant.activo,
                'attribute_options': {}, 
                'images': [img.image.url for img in variant.specific_images.all()]
            }
            visual_value_id = None
            for option in variant.options.all():
                variant_dict['attribute_options'][option.attribute.slug] = option.value
                if option.attribute.slug == visual_attribute_slug:
                    visual_value_id = option.id
            
            if visual_value_id and visual_value_id in attribute_images_map:
                variant_dict['images'] = attribute_images_map[visual_value_id]

            if product.acepta_cuotas and variant.precio_variante and product.numero_de_cuotas > 0:
                cuota_mensual = variant.precio_variante / product.numero_de_cuotas
                variant_dict['cuotas'] = {'numero': product.numero_de_cuotas, 'monto_mensual': f"{cuota_mensual:.2f}"}
            
            variants_data['variants'].append(variant_dict)
            
        default_variant = variants_queryset.filter(stock_disponible__gt=0).first() or variants_queryset.first()
        if default_variant:
            variants_data['default_variant_id'] = default_variant.id

        context['variants_data_json'] = variants_data
        return context
    
# =============================================================================
#  VISTA DE OFERTAS
# =============================================================================
def sale_product_list_view(request):
    prefetch_images = Prefetch(
        'product__attribute_images',
        queryset=AttributeImage.objects.select_related('attribute_value').order_by('orden_visualizacion'),
        to_attr='prefetched_images'
    )

    all_sale_variants = ProductVariant.objects.filter(
        activo=True, stock_disponible__gt=0, product__activo=True,
        precio_variante__lt=F('product__precio_base')
    ).select_related(
        'product', 'product__brand', 'product__supplier', 'product__visual_attribute'
    ).prefetch_related(
        'options__attribute', prefetch_images
    ).order_by('-product__destacado', '-product__creado')

    paginator = Paginator(all_sale_variants, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'titulo_pagina': "Ofertas Imperdibles"
    }
    return render(request, 'myproducts/sale_list.html', context)

class CategoryListView(ListView):
    model = Categoria
    template_name = 'myproducts/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        # Solo queremos mostrar las categorías principales, las que no tienen padre.
        # El prefetch_related es una optimización para cargar las imágenes de forma eficiente.
        return Categoria.objects.filter(padre__isnull=True).prefetch_related('subcategorias').order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Explora Nuestras Categorías"
        return context

