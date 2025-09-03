# mysales/admin.py

from django.contrib import admin
from .models import Order, OrderItem, SalePayment, InstallmentSale, InstallmentPayment
from django.utils.html import format_html
from django.urls import reverse

# =============================================================================
#  INLINES (Secciones que aparecen dentro de otros modelos)
# =============================================================================
class SalePaymentInline(admin.TabularInline):
    model = SalePayment
    extra = 0
    fields = ('payment_date', 'amount', 'payment_method', 'reference_code', 'receipt_file', 'notes')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ('variant', 'nombre_producto', 'precio_base_producto', 'precio_unitario_variante', 'cantidad', 'proveedor_producto', 'get_costo_total_display')
    readonly_fields = ('nombre_producto', 'precio_base_producto', 'precio_unitario_variante', 'proveedor_producto', 'get_costo_total_display')
    extra = 1
    raw_id_fields = ['variant']

    def get_costo_total_display(self, obj):
        if obj and hasattr(obj, 'get_costo_total'):
            return f"S/. {obj.get_costo_total():.2f}"
        return "S/. 0.00"
    get_costo_total_display.short_description = 'Total Ítem'

class InstallmentPaymentInline(admin.TabularInline):
    model = InstallmentPayment
    extra = 1

    fields = ('payment_date', 'amount_paid', 'receipt_file', 'notes', 'receipt_pdf_link')
    readonly_fields = ('receipt_pdf_link',) # Hacemos que el enlace sea de solo lectura

    # --- ¡CAMBIO 2: La función que crea el enlace de descarga! ---
    def receipt_pdf_link(self, obj):
        # El 'obj' aquí es una instancia de InstallmentPayment
        if obj.pk: # Solo mostramos el enlace si el pago ya ha sido guardado
            url = reverse('mysales:installment_payment_receipt_pdf', args=[obj.id])
            return format_html('<a href="{}" class="button" target="_blank">Recibo PDF</a>', url)
        return "Guarda para generar el recibo" # Mensaje para pagos nuevos
    receipt_pdf_link.short_description = 'Descargar Recibo'

# =============================================================================
#  ADMIN PARA VENTAS AL CONTADO
# =============================================================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id_display', 
        'user_display', 
        'fecha_pedido', 
        'estado_pedido',
        'total_pedido_display', 
        'pagado', 
        'activo',
        'invoice_pdf_link'
    )
    list_filter = ('estado_pedido', 'pagado', 'activo', 'fecha_pedido', 'metodo_pago', 'tipo_comprobante')
    search_fields = (
        'id__iexact', 'user__username', 'email_cliente', 'nombre_cliente', 'dni_cliente',
        'ruc', 'razon_social',
        'items__variant__product__nombre'
    )
    inlines = [OrderItemInline, SalePaymentInline]
    list_select_related = ('user',)
    raw_id_fields = ('user',)
    
    class Media:
        js = ('admin/js/jquery.init.js', 'mysales/js/order_form.js',)

    # --- ¡CAMBIO #1: AÑADIMOS NUESTRO NUEVO BOTÓN A LOS CAMPOS DE SOLO LECTURA! ---
    def get_readonly_fields(self, request, obj=None):
        if obj:
            # Cuando una orden ya existe, añadimos el botón a la lista.
            return ['id', 'fecha_pedido', 'actualizado', 'subtotal', 'total_pedido', 'user_display_link', 'descargar_nota_venta_link','descargar_orden_pedido_link']
        return ['id', 'fecha_pedido', 'actualizado', 'subtotal', 'total_pedido']

    def get_fieldsets(self, request, obj=None):
        user_field = ('user_display_link',) if obj else ('user',)
        
        # Preparamos los fieldsets base
        fieldsets = (
            ("Información del Pedido", {'fields': ('id',) + user_field + ('fecha_pedido', 'actualizado', 'estado_pedido', 'activo')}),
            ("Datos del Cliente", {'fields': ('nombre_cliente', 'email_cliente', 'dni_cliente', 'telefono_contacto_envio')}),
            ("Dirección de Envío", {'fields': ('direccion_envio', 'ciudad_envio', 'departamento_envio', 'pais_envio')}),
            ("Datos del Comprobante", {'fields': ('tipo_comprobante', 'ruc', 'razon_social', 'direccion_fiscal')}),
            ("Información de Pago", {'fields': ('metodo_pago', 'pagado', 'id_transaccion_pago', 'payment_receipt_file')}),
            ("Totales", {'fields': ('subtotal', 'costo_envio', 'total_pedido')}),
            ("Observaciones", {'fields': ('observaciones_cliente', 'observaciones_internas')}),
        )

        # --- ¡CAMBIO #2: SI LA ORDEN EXISTE, AÑADIMOS UNA NUEVA SECCIÓN PARA ACCIONES! ---
        if obj:
            acciones_fieldset = ("Acciones Rápidas", {
                'fields': ('descargar_nota_venta_link', 'descargar_orden_pedido_link'),
                'description': 'Usa este botón para descargar la Nota de Venta y enviarla manualmente al cliente (ej. por WhatsApp).'
            })
            # Insertamos la nueva sección justo después de la información del pedido
            fieldsets_list = list(fieldsets)
            fieldsets_list.insert(1, acciones_fieldset)
            return tuple(fieldsets_list)
        
        return fieldsets


    def invoice_pdf_link(self, obj):
        url = reverse('mysales:order_invoice_pdf', args=[obj.id])
        return format_html('<a href="{}" class="button" target="_blank">Generar Comprobante Fiscal</a>', url)
    invoice_pdf_link.short_description = 'Comprobante Fiscal (Boleta/Factura)'  
    
    # --- ¡CAMBIO #3: ESTA ES LA FUNCIÓN QUE CREA NUESTRO BOTÓN MÁGICO! ---
    def descargar_nota_venta_link(self, obj):
        # Usamos 'reverse' para obtener la URL correcta de nuestra vista de Nota de Venta
        url = reverse('mysales:order_nota_venta_pdf', args=[obj.id])
        # Devolvemos el enlace HTML con el estilo de un botón del admin
        return format_html('<a href="{}" class="button" target="_blank">Descargar Nota de Venta (PDF)</a>', url)
    descargar_nota_venta_link.short_description = 'Nota de Venta para Cliente'
    
    def user_display(self, obj):
        return obj.user.username if obj.user else obj.nombre_cliente or "Invitado"
    user_display.short_description = "Cliente"

    def total_pedido_display(self, obj):
        return f"S/. {obj.total_pedido:.2f}"
    total_pedido_display.short_description = "Total"
    total_pedido_display.admin_order_field = 'total_pedido'

    def user_display_link(self, obj):
        if obj.user:
            link = reverse("admin:auth_user_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', link, obj.user.username)
        return obj.nombre_cliente or "N/A"
    user_display_link.short_description = "Cliente (Usuario)"

    def save_model(self, request, obj, form, change):
        if obj.user:
            if not obj.nombre_cliente: obj.nombre_cliente = obj.user.get_full_name() or obj.user.username
            if not obj.email_cliente: obj.email_cliente = obj.user.email
            if hasattr(obj.user, 'customerprofile') and not obj.dni_cliente: obj.dni_cliente = obj.user.customerprofile.DNI
        super().save_model(request, obj, form, change)
        obj.calcular_totales()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.calcular_totales()

    def descargar_orden_pedido_link(self, obj):
    # Apuntamos a la nueva URL 'order_pedido_pdf'
        url = reverse('mysales:order_pedido_pdf', args=[obj.id])
        # Cambiamos el texto del botón
        return format_html('<a href="{}" class="button" target="_blank">PDF de Pedido (para cliente)</a>', url)
    descargar_orden_pedido_link.short_description = 'Orden de Pedido'

      

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_id_display', 'product_display', 'cantidad', 'precio_unitario_variante', 'get_costo_total')
    readonly_fields = ('order', 'variant', 'nombre_producto', 'precio_unitario_variante', 'precio_base_producto', 'proveedor_producto')
    search_fields = ('order__id__istartswith', 'variant__product__nombre', 'nombre_producto')
    list_filter = ('variant__product__categoria',)
    raw_id_fields = ('order', 'variant',)

    def order_id_display(self, obj):
        return obj.order.id_display
    order_id_display.short_description = "ID Pedido"

    def product_display(self, obj):
        return str(obj.variant) if obj.variant else obj.nombre_producto
    product_display.short_description = "Producto (Variante)"

# =============================================================================
#  ADMIN PARA VENTAS A CRÉDITO (LA NUEVA PESTAÑA)
# =============================================================================
@admin.register(InstallmentSale)
class InstallmentSaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'variant', 'sale_date', 'status', 'total_credit_price', 'agreement_pdf_link')
    list_filter = ('status', 'sale_date')
    search_fields = ('customer_name', 'customer_dni', 'user__username', 'variant__product__nombre')
    raw_id_fields = ('user', 'variant')
    inlines = [InstallmentPaymentInline]
    readonly_fields = ('total_credit_price', 'created_at', 'updated_at')
    
    fieldsets = (
        ("Información del Cliente", {
            'description': "Selecciona un cliente registrado (y los campos de abajo se llenarán solos al guardar) O llena los datos manualmente para un cliente nuevo.",
            'fields': ('user', ('customer_name', 'customer_dni'), ('customer_phone', 'customer_email'))
        }),
        ("Detalles del Producto y Acuerdo", {
            'fields': ('variant', 'sale_date', 'fecha_primer_pago', 'status')
        }),
        ("Términos del Crédito", {
            'fields': ('product_cash_price', 'initial_payment', 'interest_rate', 'number_of_installments', 'installment_amount', 'total_credit_price')
        }),
        ("Notas y Auditoría", {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # --- ¡AQUÍ ESTÁ LA LÓGICA DE AUTO-RELLENO! ---
    def save_model(self, request, obj, form, change):
        # Si se seleccionó un usuario...
        if obj.user:
            # ...y los campos manuales están vacíos, los llenamos.
            if not obj.customer_name:
                obj.customer_name = obj.user.get_full_name() or obj.user.username
            if not obj.customer_email:
                obj.customer_email = obj.user.email
            # Asumimos que el perfil de cliente existe
            if hasattr(obj.user, 'customerprofile'):
                if not obj.customer_dni:
                    obj.customer_dni = obj.user.customerprofile.DNI
                if not obj.customer_phone:
                    obj.customer_phone = obj.user.customerprofile.telefono
        
        super().save_model(request, obj, form, change)

    def agreement_pdf_link(self, obj):
        url = reverse('mysales:installment_sale_agreement_pdf', args=[obj.id])
        return format_html('<a href="{}" class="button" target="_blank">Acuerdo PDF</a>', url)
    agreement_pdf_link.short_description = 'Acuerdo PDF'