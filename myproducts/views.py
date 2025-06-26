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

class ProductCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'myproducts/product_form.html'
    success_message = "Producto '%(nombre)s' creado exitosamente."

    def get_success_url(self):
        # Redirige al detalle del producto recién creado
        return reverse_lazy('myproducts:product_detail', kwargs={'slug': self.object.slug})

    def form_valid(self, form):
        # form.instance.creador = self.request.user # Si quieres asignar el usuario que lo crea
        messages.success(self.request, f"Producto '{form.cleaned_data.get('nombre')}' creado exitosamente.")
        return super().form_valid(form)

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

    def form_valid(self, form):
        messages.success(self.request, f"Producto '{form.cleaned_data.get('nombre')}' actualizado exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f"Editar Producto: {self.object.nombre}"
        context['nombre_boton'] = "Actualizar Producto"
        return context
    
class ProductDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView): # <--- NOMBRE NUEVO Y MIXINS ADECUADOS
    model = Product
    template_name = 'myproducts/product_confirm_delete.html'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('myproducts:product_list')

    def get_success_message(self, cleaned_data):
        return f"Producto '{self.object.nombre}' eliminado exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f"Eliminar Producto: {self.object.nombre}"
        return context 

class ProductSearchView(ListView):
    model = Product
    template_name = 'myproducts/product_search_results.html'
    context_object_name = 'productos'
    paginate_by = 16  # ¡Paginación gratis! Ajusta el número como quieras.

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if not query:
            return Product.objects.none()  # No mostrar nada si no hay búsqueda

        # 1. FILTRAR
        search_results = Product.objects.filter(
            Q(nombre__icontains=query) | 
            Q(descripcion__icontains=query) |
            Q(brand__nombre__icontains=query) |
            Q(categoria__nombre__icontains=query) |
            Q(variants__sku__icontains=query)
        ).filter(activo=True).distinct()

        # 2. OPTIMIZAR (Lógica de ProductListView)
        return search_results.annotate(
            min_variant_price=Min('variants__precio_variante', filter=Q(variants__activo=True, variants__stock_disponible__gt=0))
        ).prefetch_related(
            Prefetch(
                'variants',
                queryset=ProductVariant.objects.filter(activo=True).prefetch_related('options__attribute'),
                to_attr='active_variants'
            )
        )

    def get_context_data(self, **kwargs):
        # Primero, obtenemos el contexto base de ListView
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()

        # 3. PROCESAR (Lógica de ProductListView)
        color_attribute_slug = 'color'
        product_ids = [p.id for p in context['productos']]

        images_map = defaultdict(lambda: defaultdict(list))
        attr_images = AttributeImage.objects.filter(
            product_id__in=product_ids,
            attribute_value__attribute__slug=color_attribute_slug
        ).select_related('attribute_value').order_by('orden_visualizacion')

        for img in attr_images:
            images_map[img.product_id][img.attribute_value.value].append(img.image.url)

        for producto in context['productos']:
            # Asignar variante y demás atributos extra
            if hasattr(producto, 'active_variants'):
                sorted_variants = sorted(producto.active_variants, key=lambda v: v.precio_variante)
                producto.variant_to_display = sorted_variants[0] if sorted_variants else None
            else:
                producto.variant_to_display = None
            
            producto.main_image_url = ''
            if producto.variant_to_display:
                color_opt = next((opt for opt in producto.variant_to_display.options.all() if opt.attribute.slug == color_attribute_slug), None)
                if color_opt and images_map[producto.id][color_opt.value]:
                    producto.main_image_url = images_map[producto.id][color_opt.value][0]
            if not producto.main_image_url:
                 first_img = AttributeImage.objects.filter(product=producto).first()
                 if first_img:
                    producto.main_image_url = first_img.image.url

            producto.color_info = []
            unique_colors_set = set()
            if hasattr(producto, 'active_variants'):
                for variant in producto.active_variants:
                    for option in variant.options.all():
                        if option.attribute.slug == color_attribute_slug and option.value not in unique_colors_set:
                            unique_colors_set.add(option.value)
                            all_images_for_color = images_map.get(producto.id, {}).get(option.value, [])
                            if all_images_for_color:
                                producto.color_info.append({
                                    'name': option.value,
                                    'code': option.color_code,
                                    'images': all_images_for_color
                                })
        
        # 4. AÑADIR VARIABLES EXTRA AL CONTEXTO
        context['query'] = query
        context['search_performed'] = bool(query)
        context['titulo_pagina'] = f"Resultados para '{query}'"
        
        return context

class ProductListView(ListView):
    model = Product
    template_name = 'myproducts/product_list.html'
    context_object_name = 'productos'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(activo=True)
        self.categoria_actual = None
        
        # --- INICIO DE LA LÓGICA CORREGIDA ---
        category_path = self.kwargs.get('category_path')
        if category_path:
            # Dividimos la ruta por las barras para obtener los slugs individuales
            slugs = category_path.split('/')
            
            # Recorremos la jerarquía para encontrar la categoría nieta correcta
            parent = None
            for slug in slugs:
                # Buscamos la categoría por su slug y asegurándonos que tenga el padre correcto
                self.categoria_actual = get_object_or_404(Categoria, slug=slug, padre=parent)
                # La categoría que acabamos de encontrar será el padre de la siguiente en el bucle
                parent = self.categoria_actual
        # --- FIN DE LA LÓGICA CORREGIDA ---

        # El resto de tu función funciona perfectamente con la categoría ya encontrada
        if self.categoria_actual:
            queryset = queryset.filter(categoria_id__in=self.categoria_actual.get_descendant_ids())
        
        queryset = queryset.annotate(
            min_variant_price=Min('variants__precio_variante', filter=Q(variants__activo=True, variants__stock_disponible__gt=0))
        ).prefetch_related(
            Prefetch(
                'variants',
                queryset=ProductVariant.objects.filter(activo=True).prefetch_related('options__attribute'),
                to_attr='active_variants'
            )
        )
        return queryset.order_by('-destacado', '-creado')   

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categoria_actual'] = self.categoria_actual
        
        color_attribute_slug = 'color'
        product_ids = [p.id for p in context['productos']]

        # 1. Mapear todas las imágenes de una vez para ser eficientes
        images_map = defaultdict(lambda: defaultdict(list))
        attr_images = AttributeImage.objects.filter(
            product_id__in=product_ids,
            attribute_value__attribute__slug=color_attribute_slug
        ).select_related('attribute_value').order_by('orden_visualizacion')

        for img in attr_images:
            images_map[img.product_id][img.attribute_value.value].append(img.image.url)

        # 2. ÚNICO BUCLE para procesar cada producto y añadirle la info extra
        for producto in context['productos']:
            # Asignar la variante a mostrar (la más barata disponible)
            sorted_variants = sorted(producto.active_variants, key=lambda v: v.precio_variante)
            producto.variant_to_display = sorted_variants[0] if sorted_variants else None
            
            # Obtener la imagen principal a partir de la variante a mostrar
            producto.main_image_url = ''
            if producto.variant_to_display:
                first_variant_color = None
                for opt in producto.variant_to_display.options.all():
                    if opt.attribute.slug == color_attribute_slug:
                        first_variant_color = opt.value
                        break
                if first_variant_color and images_map[producto.id][first_variant_color]:
                    producto.main_image_url = images_map[producto.id][first_variant_color][0]

            # Recopilar información de colores (nombre, código, lista de imágenes)
            producto.color_info = []
            unique_colors_set = set() # <--- INICIALIZAMOS AQUÍ, ANTES DE USARLA
            
            for variant in producto.active_variants:
                for option in variant.options.all():
                    # Ahora la comprobación funciona porque 'unique_colors_set' ya existe
                    if option.attribute.slug == color_attribute_slug and option.value not in unique_colors_set:
                        unique_colors_set.add(option.value)
                        
                        all_images_for_color = images_map.get(producto.id, {}).get(option.value, [])
                        
                        if all_images_for_color:
                            producto.color_info.append({
                                'name': option.value,
                                'code': option.color_code,
                                'images': all_images_for_color
                            })
        
        # Lógica de breadcrumbs (fuera del bucle)
        if self.categoria_actual:
            ruta_categoria = []
            cat_temp = self.categoria_actual
            while cat_temp:
                ruta_categoria.append(cat_temp)
                cat_temp = cat_temp.padre
            context['ruta_categoria'] = reversed(ruta_categoria)
            
        return context


class ProductListByBrandView(ListView):
    model = Product
    template_name = 'myproducts/product_list_by_brand.html'
    context_object_name = 'productos'
    paginate_by = 12 # O el número que prefieras

    def get_queryset(self):
        # Primero, filtramos por la marca, que es lo específico de esta vista
        self.brand = get_object_or_404(Brand, slug=self.kwargs['brand_slug'])
        queryset = Product.objects.filter(brand=self.brand, activo=True)

        # AHORA, AÑADIMOS TODA LA LÓGICA DE OPTIMIZACIÓN
        queryset = queryset.annotate(
            min_variant_price=Min('variants__precio_variante', filter=Q(variants__activo=True, variants__stock_disponible__gt=0))
        ).prefetch_related(
            Prefetch(
                'variants',
                queryset=ProductVariant.objects.filter(activo=True).prefetch_related('options__attribute'),
                to_attr='active_variants'
            )
        )
        return queryset.order_by('-creado')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_brand'] = self.brand
        context['page_title'] = f"Productos de la marca {self.brand.nombre}"
        
        # --- COPIAMOS LA LÓGICA DE PROCESAMIENTO DE IMÁGENES Y COLORES ---
        color_attribute_slug = 'color'
        product_ids = [p.id for p in context['productos']]

        images_map = defaultdict(lambda: defaultdict(list))
        attr_images = AttributeImage.objects.filter(
            product_id__in=product_ids,
            attribute_value__attribute__slug=color_attribute_slug
        ).select_related('attribute_value').order_by('orden_visualizacion')

        for img in attr_images:
            images_map[img.product_id][img.attribute_value.value].append(img.image.url)

        for producto in context['productos']:
            sorted_variants = sorted(producto.active_variants, key=lambda v: v.precio_variante)
            producto.variant_to_display = sorted_variants[0] if sorted_variants else None
            
            producto.main_image_url = ''
            if producto.variant_to_display:
                first_variant_color = None
                for opt in producto.variant_to_display.options.all():
                    if opt.attribute.slug == color_attribute_slug:
                        first_variant_color = opt.value
                        break
                if first_variant_color and images_map[producto.id][first_variant_color]:
                    producto.main_image_url = images_map[producto.id][first_variant_color][0]

            producto.color_info = []
            unique_colors_set = set()
            
            for variant in producto.active_variants:
                for option in variant.options.all():
                    if option.attribute.slug == color_attribute_slug and option.value not in unique_colors_set:
                        unique_colors_set.add(option.value)
                        all_images_for_color = images_map.get(producto.id, {}).get(option.value, [])
                        if all_images_for_color:
                            producto.color_info.append({
                                'name': option.value,
                                'code': option.color_code,
                                'images': all_images_for_color
                            })
        return context

# Vista para listar productos por PROVEEDOR
class ProductListBySupplierView(ListView):
    model = Product
    template_name = 'myproducts/product_list_by_supplier.html'
    context_object_name = 'productos'
    paginate_by = 12

    def get_queryset(self):
        # Filtramos por proveedor
        self.supplier = get_object_or_404(Supplier, pk=self.kwargs['supplier_pk'])
        queryset = Product.objects.filter(supplier=self.supplier, activo=True)

        # AÑADIMOS LA LÓGICA DE OPTIMIZACIÓN
        queryset = queryset.annotate(
            min_variant_price=Min('variants__precio_variante', filter=Q(variants__activo=True, variants__stock_disponible__gt=0))
        ).prefetch_related(
            Prefetch(
                'variants',
                queryset=ProductVariant.objects.filter(activo=True).prefetch_related('options__attribute'),
                to_attr='active_variants'
            )
        )
        return queryset.order_by('-creado')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supplier'] = self.supplier
        context['page_title'] = f"Productos de {self.supplier.nombre_empresa}"
        
        # --- COPIAMOS LA LÓGICA DE PROCESAMIENTO DE IMÁGENES Y COLORES ---
        color_attribute_slug = 'color'
        product_ids = [p.id for p in context['productos']]

        images_map = defaultdict(lambda: defaultdict(list))
        attr_images = AttributeImage.objects.filter(
            product_id__in=product_ids,
            attribute_value__attribute__slug=color_attribute_slug
        ).select_related('attribute_value').order_by('orden_visualizacion')

        for img in attr_images:
            images_map[img.product_id][img.attribute_value.value].append(img.image.url)

        for producto in context['productos']:
            sorted_variants = sorted(producto.active_variants, key=lambda v: v.precio_variante)
            producto.variant_to_display = sorted_variants[0] if sorted_variants else None
            
            producto.main_image_url = ''
            if producto.variant_to_display:
                first_variant_color = None
                for opt in producto.variant_to_display.options.all():
                    if opt.attribute.slug == color_attribute_slug:
                        first_variant_color = opt.value
                        break
                if first_variant_color and images_map[producto.id][first_variant_color]:
                    producto.main_image_url = images_map[producto.id][first_variant_color][0]

            producto.color_info = []
            unique_colors_set = set()
            
            for variant in producto.active_variants:
                for option in variant.options.all():
                    if option.attribute.slug == color_attribute_slug and option.value not in unique_colors_set:
                        unique_colors_set.add(option.value)
                        all_images_for_color = images_map.get(producto.id, {}).get(option.value, [])
                        if all_images_for_color:
                            producto.color_info.append({
                                'name': option.value,
                                'code': option.color_code,
                                'images': all_images_for_color
                            })     
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'myproducts/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()


        # 1. OBTENER VARIANTES ACTIVAS
        variants_queryset = product.variants.filter(activo=True).prefetch_related('options__attribute')

        # Si no hay variantes activas, no podemos continuar.
        if not variants_queryset.exists():
            context['variants_data_json'] = json.dumps({'variants': []})
            return context

        # 2. MAPEAR IMÁGENES POR VALOR DE ATRIBUTO (COLOR)
        attribute_images_map = defaultdict(list)
        color_attribute_slug = 'color'  # Asumimos que el slug de tu atributo de color es 'color'
        
        image_query = AttributeImage.objects.filter(
            product=product,
            attribute_value__attribute__slug=color_attribute_slug
        ).order_by('orden_visualizacion')

        for attr_img in image_query:
            attribute_images_map[attr_img.attribute_value_id].append(attr_img.image.url)

        # 3. PREPARAR DATOS PARA JSON
        variants_data = {
            'attributes_definition': [],
            'variants': [],
            'product_base_price': str(product.precio_base) if product.precio_base else None,
            'default_variant_id': None
        }
        
        # 4. DEFINIR ATRIBUTOS Y SUS OPCIONES DISPONIBLES
        for attribute in product.configurable_attributes.all().order_by('nombre'):
            options = sorted(list(
                variants_queryset.filter(options__attribute=attribute)
                                 .values_list('options__value', flat=True)
                                 .distinct()
            ))
            
            if options:
                if attribute.slug == 'talla':
                    size_order = ['S', 'M', 'L', 'XL', '2XL', '3XL']
                    options.sort(key=lambda s: size_order.index(s) if s in size_order else float('inf'))
                
                variants_data['attributes_definition'].append({
                    'id_slug': attribute.slug,
                    'name': attribute.nombre,
                    'type': 'image_swatch' if attribute.slug == color_attribute_slug else 'button',
                    'options_display_order': options
                })
        
        # 5. SERIALIZAR CADA VARIANTE
        for variant in variants_queryset:
            variant_dict = {
                'id': variant.id,
                'sku': variant.sku,
                'price': str(variant.precio_variante),
                'stock': variant.stock_disponible,
                'is_active': variant.activo,
                'attribute_options': {},
                'images': []
            }
            color_value_id = None
            for option in variant.options.all():
                variant_dict['attribute_options'][option.attribute.slug] = option.value
                if option.attribute.slug == color_attribute_slug:
                    color_value_id = option.id
            
            if color_value_id and color_value_id in attribute_images_map:
                variant_dict['images'] = attribute_images_map[color_value_id]

            if product.acepta_cuotas and variant.precio_variante and product.numero_de_cuotas > 0:
                cuota_mensual = variant.precio_variante / product.numero_de_cuotas
                variant_dict['cuotas'] = {
                    'numero': product.numero_de_cuotas,
                    'monto_mensual': f"{cuota_mensual:.2f}"
                }
            
            variants_data['variants'].append(variant_dict)
            

        # 6. ESTABLECER VARIANTE POR DEFECTO
        # La primera variante activa con stock es una buena candidata
        default_variant = variants_queryset.filter(stock_disponible__gt=0).first()
        if not default_variant:
            default_variant = variants_queryset.first() # Fallback a la primera activa
        
        if default_variant:
            variants_data['default_variant_id'] = default_variant.id

        # 7. FINALIZAR CONTEXTO
        # en la penúltima línea de get_context_data...
        context['variants_data_json'] = variants_data # <--- ¡SOLO EL DICCIONARIO!
        return context
    
def sale_product_list_view(request):
    """
    Muestra una lista de VARIANTES en oferta y precarga los datos necesarios
    para que la tarjeta pueda construir un carrusel de imágenes.
    AHORA CON PAGINACIÓN.
    """
    
    # Preparamos un prefetch para las imágenes, ya ordenadas
    prefetch_images = Prefetch(
        'product__attribute_images',
        queryset=AttributeImage.objects.order_by('orden_visualizacion'),
        to_attr='prefetched_images'
    )

    # 1. Obtenemos TODAS las variantes en oferta, como antes
    all_sale_variants = ProductVariant.objects.filter(
        activo=True,
        stock_disponible__gt=0,
        product__activo=True,
        precio_variante__lt=F('product__precio_base')
    ).select_related(
        'product', 'product__brand', 'product__supplier'
    ).prefetch_related(
        'options__attribute',
        prefetch_images
    ).order_by('-product__destacado', '-product__creado')

    # 2. APLICAMOS LA PAGINACIÓN
    paginator = Paginator(all_sale_variants, 12) # Muestra 12 ofertas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 3. PASAMOS EL OBJETO DE PÁGINA AL CONTEXTO
    # La plantilla ahora usará 'page_obj' para el bucle for
    context = {
        'page_obj': page_obj, # ¡LA CLAVE ESTÁ AQUÍ!
        'is_paginated': page_obj.has_other_pages(), # Le decimos a la plantilla si hay más de una página
        'paginator': paginator, # Pasamos el paginador para la lógica de los números
        'titulo_pagina': "Ofertas Imperdibles"
    }
    return render(request, 'myproducts/sale_list.html', context)