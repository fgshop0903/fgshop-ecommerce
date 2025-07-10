# myproducts/admin.py

import json
from itertools import product as cartesian_product

from django.contrib import admin, messages
from django.db import transaction
from django.urls import reverse, path
from django.utils.html import format_html
from django.shortcuts import render, redirect, get_object_or_404
from .models import (
    Attribute, AttributeImage, AttributeValue, Brand, Categoria,
    EspecificacionPlantilla, Product, ProductVariant, Supplier
)
from .forms import VariantCombinationForm 
from django.db.models import Count
import pandas as pd
from .forms import ProductImportForm


# =============================================================================
# 1. ACCIONES Y CLASES 'INLINE' (Se definen primero para poder usarlas después)
# =============================================================================

@admin.action(description="Generar/Actualizar variantes a partir de atributos")
def generate_variants_action(modeladmin, request, queryset):
    for product_obj in queryset:
        configurable_attributes = product_obj.configurable_attributes.all().order_by('nombre')
        if not configurable_attributes:
            modeladmin.message_user(request, f"'{product_obj.nombre}' no tiene atributos configurables.", level='WARNING')
            continue
        value_lists = [list(AttributeValue.objects.filter(attribute=attr)) for attr in configurable_attributes]
        if not all(value_lists):
            modeladmin.message_user(request, f"Atributos de '{product_obj.nombre}' no tienen valores.", level='ERROR')
            continue
        all_combinations = list(cartesian_product(*value_lists))
        with transaction.atomic():
            product_obj.variants.all().delete()
            created_count = 0
            for combination in all_combinations:
                new_variant = ProductVariant(product=product_obj, precio_variante=product_obj.precio_base or 0.00)
                options_list = [str(opt.value) for opt in combination]
                new_variant.nombre_variante = " / ".join(options_list)
                new_variant.save()
                new_variant.options.set(combination)
                new_variant.sku = f"FG-{new_variant.product.pk}-{new_variant.pk + 1000:04d}"
                new_variant.save(update_fields=['sku'])
                created_count += 1
        modeladmin.message_user(request, f"Para '{product_obj.nombre}': Se crearon {created_count} nuevas variantes.", level='SUCCESS')

class AttributeImageInline(admin.TabularInline):
    model = AttributeImage
    extra = 1
    verbose_name_plural = "Gestión de Imágenes (Estándar o por Variante)"
    fields = ('image_preview', 'image', 'variant', 'attribute_value', 'orden_visualizacion', 'alt_text')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        return format_html(f'<img src="{obj.image.url}" width="100"/>') if obj.image else "(Sin imagen)"
    image_preview.short_description = "Vista Previa"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        object_id = request.resolver_match.kwargs.get('object_id')
        if not object_id:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        
        product = get_object_or_404(Product, pk=object_id)
        
        # Filtramos el dropdown de 'attribute_value' como antes
        if db_field.name == "attribute_value":
            kwargs["queryset"] = AttributeValue.objects.filter(attribute__in=product.configurable_attributes.all())
        
        # --- AÑADIMOS ESTO PARA FILTRAR EL DROPDOWN DE VARIANTES ---
        if db_field.name == "variant":
            kwargs["queryset"] = ProductVariant.objects.filter(product=product)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ('nombre_variante', 'sku', 'precio_variante', 'stock_disponible', 'activo')
    readonly_fields = ('nombre_variante', 'sku')
    verbose_name_plural = "2. Variantes Generadas (Ajustes Rápidos)"
    can_delete = False
    show_change_link = True

# =============================================================================
# 2. CONFIGURACIÓN DE ADMIN PRINCIPALES
# =============================================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio_base', 'activo', 'variants_count_display')
    list_filter = ('activo', 'destacado', 'categoria', 'acepta_cuotas')
    search_fields = ('nombre',)
    prepopulated_fields = {'slug': ('nombre',)}
    actions = ['redirect_to_generate_specifics']
    inlines = [AttributeImageInline, ProductVariantInline]
    
    fieldsets = (
        ("Información General", {
            'fields': ('nombre', 'slug', 'categoria', 'brand', 'supplier', ('activo', 'destacado'))
        }),
        ("Configuración de Imágenes y Variantes", {
            'fields': (
                'use_variant_specific_images', 
                'visual_attribute', 
                'configurable_attributes',
            ), 
            'description': "Selecciona el modo de imagen y los atributos. Guarda. Luego gestiona las imágenes abajo o usa las acciones del menú."
        }),
        ("Descripción y Especificaciones", {
            'classes': ('collapse',),
            'fields': ('descripcion', 'especificaciones'),
        }),
        ("Precio y Pagos", {
            'fields': ('precio_base', 'acepta_cuotas', 'numero_de_cuotas', 'calculo_cuota_mensual'),
        }),
    )
    
    readonly_fields = ('calculo_cuota_mensual',)

    class Media:
        js = ('myproducts/js/admin_spec_loader.js',)

    def get_urls(self):
        """
        Añadimos dos URLs: una para generar variantes y OTRA para importar.
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:product_id>/generate-specific-variants/',
                self.admin_site.admin_view(self.generate_specific_variants_view),
                name='product_generate_specific_variants',
            ),
            path(
                'import-products/',
                self.admin_site.admin_view(self.import_products_view),
                name='product_import',
            )
        ]
        return custom_urls + urls
    
    def import_products_view(self, request):
        """
        Esta vista maneja la página de importación de productos desde Excel.
        """
        if request.method == 'POST':
            form = ProductImportForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['file']
                try:
                    df = pd.read_excel(file)
                    # --- Procesamos el archivo ---
                    self.process_excel_file(request, df)
                    return redirect(reverse('admin:myproducts_product_changelist'))
                except Exception as e:
                    self.message_user(request, f"Error al procesar el archivo: {e}", messages.ERROR)
        else:
            form = ProductImportForm()

        context = {
            **self.admin_site.each_context(request),
            'title': 'Importar Productos desde Excel',
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/import_form.html', context)
    
    def process_excel_file(self, request, df):
        created_products_count = 0
        updated_products_count = 0
        created_variants_count = 0
        updated_variants_count = 0
        newly_created_product_pks = [] # Lista para guardar los IDs de productos nuevos
        
        try:
            with transaction.atomic():
                for index, row in df.iterrows():
                    # ... (Lógica de categoría, brand, supplier)
                    categoria_path, category_names, parent_category, final_category, brand, supplier, product_name = self.get_related_data(row)

                    product, product_created = Product.objects.update_or_create(
                        nombre__iexact=product_name,
                        defaults={
                            'nombre': product_name, 'descripcion': row.get('product_descripcion', ''),
                            'categoria': final_category, 'brand': brand, 'supplier': supplier,
                            'precio_base': row.get('product_precio_base', 0.00)
                        }
                    )
                    
                    if product_created:
                        newly_created_product_pks.append(product.pk)
                        created_products_count += 1
                    else:
                        updated_products_count +=1
                    
                    # ... (lógica de variantes)
                    variant_options, variant_name = self.get_variant_options(row)
                    variant, variant_created = ProductVariant.objects.update_or_create(
                        product=product, nombre_variante=variant_name,
                        defaults={
                            'precio_variante': row['variante_precio'],
                            'stock_disponible': row['variante_stock']
                        }
                    )
                    if variant_created and not variant.sku:
                        variant.sku = f"FG-{variant.product.id:04d}-{variant.id:06d}"
                        variant.save(update_fields=['sku'])
                    variant.options.set(variant_options)
                    if variant_created: created_variants_count += 1
                    else: updated_variants_count += 1

            # Después de que la transacción es exitosa, desactivamos los productos nuevos
            if newly_created_product_pks:
                Product.objects.filter(pk__in=newly_created_product_pks).update(activo=False)

        except Exception as e:
            # ... (manejo de errores)
            self.message_user(request, f"Error en la fila {index + 2} del Excel: {e}", messages.ERROR)
            return # Salimos para no mostrar el mensaje de éxito

        success_message = (
            f"Importación exitosa. Productos: {created_products_count} creados (y desactivados), {updated_products_count} actualizados. "
            f"Variantes: {created_variants_count} creadas, {updated_variants_count} actualizadas."
        )
        self.message_user(request, success_message, messages.SUCCESS)

    def get_related_data(self, row): # Helper function
        # ... (código para obtener categoría, brand, etc.)
        # Esto es solo para hacer el código principal más limpio
        categoria_path = str(row['product_categoria']).strip()
        category_names = [name.strip() for name in categoria_path.split('>')]
        parent_category = None
        for category_name in category_names:
            category, _ = Categoria.objects.get_or_create(nombre__iexact=category_name, padre=parent_category, defaults={'nombre': category_name})
            parent_category = category
        final_category = parent_category
        brand_name = str(row['product_brand']).strip()
        supplier_name = str(row['product_supplier']).strip()
        brand, _ = Brand.objects.get_or_create(nombre__iexact=brand_name, defaults={'nombre': brand_name})
        try:
            supplier = Supplier.objects.get(nombre_empresa__iexact=supplier_name)
        except Supplier.DoesNotExist:
            raise Exception(f"El proveedor '{supplier_name}' no se encuentra registrado.")
        product_name = str(row['product_nombre']).strip()
        return categoria_path, category_names, parent_category, final_category, brand, supplier, product_name
    
    def get_variant_options(self, row): # Helper function
        # ... (código para obtener las opciones de la variante)
        variant_options = []
        for col_name in row.index:
            if str(col_name).startswith('attr_'):
                attr_name = col_name.replace('attr_', '').strip()
                attr_value_name = row[col_name]
                if pd.notna(attr_value_name):
                    attribute, _ = Attribute.objects.get_or_create(nombre=attr_name)
                    attribute_value, _ = AttributeValue.objects.get_or_create(
                        attribute=attribute, value__iexact=str(attr_value_name).strip(),
                        defaults={'value': str(attr_value_name).strip()}
                    )
                    variant_options.append(attribute_value)
        ordered_values = sorted(variant_options, key=lambda v: v.attribute.nombre)
        variant_name = " / ".join(v.value for v in ordered_values)
        return variant_options, variant_name


    def generate_specific_variants_view(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        if request.method == 'POST':
            form = VariantCombinationForm(product, request.POST)
            if form.is_valid():
                selected_lists = form.get_selected_attribute_value_lists()
                created_count, skipped_count = 0, 0
                
                with transaction.atomic():
                    for values_list in selected_lists:
                        existing_qs = product.variants.annotate(opt_count=Count('options')).filter(opt_count=len(values_list))
                        for value in values_list:
                            existing_qs = existing_qs.filter(options=value)
                        
                        if not existing_qs.exists():
                            ordered_values = sorted(values_list, key=lambda v: v.attribute.nombre)
                            variant_name = " / ".join(v.value for v in ordered_values)

                            # Creamos el objeto en memoria
                            variant = ProductVariant(
                                product=product,
                                nombre_variante=variant_name,
                                precio_variante=product.precio_base or 0.00
                            )
                            # Lo guardamos para que obtenga un PK
                            variant.save()
                            
                            # AHORA que tiene un PK, generamos el SKU
                            variant.sku = f"FG-{variant.product.id:04d}-{variant.id:06d}"
                            variant.options.set(values_list)
                            
                            # Y lo guardamos por última vez con todo
                            variant.save()
                            
                            created_count += 1
                        else:
                            skipped_count += 1
                            
                if created_count > 0:
                    self.message_user(request, f"Éxito: Se crearon {created_count} nuevas variantes.", messages.SUCCESS)
                if skipped_count > 0:
                    self.message_user(request, f"Aviso: Se omitieron {skipped_count} combinaciones que ya existían.", messages.INFO)
                
                return redirect(reverse('admin:myproducts_product_changelist'))
        else:
            form = VariantCombinationForm(product)
            has_choices = bool(form.fields['combinations'].choices)
        
        context = {
            **self.admin_site.each_context(request),
            'title': f'Generar Variantes para "{product.nombre}"',
            'product': product,
            'form': form,
            'opts': self.model._meta,
            'has_choices': has_choices,
        }
        return render(request, 'admin/generar_variantes_especificas.html', context)
    
    def variants_count_display(self, obj):
        """Este método ahora solo muestra el conteo de variantes con un link."""
        url = reverse("admin:myproducts_productvariant_changelist") + f"?product__id__exact={obj.id}"
        return format_html('<a href="{}">{} variante(s)</a>', url, obj.variants.count())
    
    variants_count_display.short_description = "Nº de Variantes"

    def render_change_form(self, request, context, **kwargs):
        templates = EspecificacionPlantilla.objects.all()
        template_data = {tpl.id: tpl.to_json_dict() for tpl in templates}
        context['spec_templates'] = templates
        context['spec_templates_json'] = json.dumps(template_data)
        return super().render_change_form(request, context, **kwargs)
    
    def calculo_cuota_mensual(self, obj):
        if obj.acepta_cuotas and obj.precio_base and obj.numero_de_cuotas > 0:
            cuota = obj.precio_base / obj.numero_de_cuotas
            return f"S/ {cuota:.2f} por mes (sobre precio base de S/ {obj.precio_base})"
        return "N/A"
    calculo_cuota_mensual.short_description = "Cálculo Cuota (Referencial)"

    def redirect_to_generate_specifics(self, request, queryset):
        """
        Esta acción redirige a la página de generación específica.
        Funciona como un puente seguro.
        """
        # 1. Verificamos que solo se haya seleccionado UN producto.
        if queryset.count() != 1:
            self.message_user(request, "Por favor, selecciona solo un producto para esta acción.", messages.ERROR)
            return

        # 2. Si se seleccionó uno, redirigimos a nuestra vista personalizada.
        product = queryset.first()
        url = reverse('admin:product_generate_specific_variants', args=[product.pk])
        return redirect(url)

    # 3. Le damos un nombre amigable para que aparezca en el dropdown.
    redirect_to_generate_specifics.short_description = "Generar variantes específicas"

    def changelist_view(self, request, extra_context=None):
        """
        Sobrescribe la vista de la lista para añadir nuestro botón de importar.
        """
        extra_context = extra_context or {}
        extra_context['import_url'] = reverse('admin:product_import')
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'product_link', 'sku', 'precio_variante', 'stock_disponible', 'activo')
    list_filter = ('activo', 'product__categoria', 'product__brand')
    search_fields = ('sku', 'nombre_variante', 'product__nombre')
    list_editable = ('precio_variante', 'stock_disponible', 'activo')
    filter_horizontal = ('options',)
    raw_id_fields = ('product',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        form.save_m2m() 
        options = obj.options.all().order_by('attribute__nombre')
        
        obj.nombre_variante = " / ".join([str(opt.value) for opt in options])
        
        if not obj.sku:
            obj.sku = f"FG-{obj.product.pk}-{obj.pk + 1000:04d}"
    
        obj.save()

    def product_link(self, obj):
        link = reverse("admin:myproducts_product_change", args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', link, obj.product.nombre)
    product_link.short_description = "Producto Maestro"



# =============================================================================
# 3. REGISTRO DE OTROS MODELOS
# =============================================================================

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug', 'logo_thumbnail')
    readonly_fields = ('logo_preview',)
    def logo_thumbnail(self, obj): return format_html(f'<img src="{obj.logo.url}" width="50"/>') if obj.logo else ""
    def logo_preview(self, obj): return format_html(f'<img src="{obj.logo.url}" width="150"/>') if obj.logo else ""

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'padre', 'slug')

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug')

@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value')
    list_filter = ('attribute',)

@admin.register(EspecificacionPlantilla)
class EspecificacionPlantillaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre', 'claves')