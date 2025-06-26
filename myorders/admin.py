from django.contrib import admin
from .models import Order, OrderItem
from django.utils.html import format_html
from django.urls import reverse

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    # --- CAMBIO ---: Usamos los nombres de campo nuevos y en el orden que quieres.
    fields = (
        'variant', 
        'nombre_producto', 
        'precio_base_producto', 
        'precio_unitario_variante', 
        'cantidad', 
        'proveedor_producto',
        'get_costo_total_display'
    )
    # --- CAMBIO ---: Hacemos de solo lectura los campos que se auto-rellenan.
    readonly_fields = (
        'nombre_producto', 
        'precio_base_producto', 
        'precio_unitario_variante', 
        'proveedor_producto', 
        'get_costo_total_display'
    )
    extra = 1 # Dejamos 1 para que sea fácil añadir el primer ítem.
    raw_id_fields = ['variant']

    def get_costo_total_display(self, obj):
        return f"S/. {obj.get_costo_total():.2f}"
    get_costo_total_display.short_description = 'Total Ítem'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id_display', 'user_display', 'fecha_pedido', 'estado_pedido',
        'total_pedido_display', 'pagado', 'activo'
    )
    list_filter = ('estado_pedido', 'pagado', 'activo', 'fecha_pedido', 'metodo_pago')
    # --- CAMBIO ---: Actualizamos el search_fields para que apunte a la ruta correcta.
    search_fields = (
        'id__iexact', 'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'email_cliente', 'nombre_cliente', 'dni_cliente',
        'items__variant__product__nombre' # Ruta corregida
    )
    inlines = [OrderItemInline]
    list_select_related = ('user',)
    raw_id_fields = ('user',)

    # Añadimos la clase Media para cargar nuestro JavaScript
    class Media:
        js = ('myorders/js/order_item_autofill.js',)

    # El resto de tu OrderAdmin ya estaba bien, lo mantenemos.
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['id', 'fecha_pedido', 'actualizado', 'subtotal', 'total_pedido', 'user_display_link']
        return ['id', 'fecha_pedido', 'actualizado', 'subtotal', 'total_pedido']

    def get_fieldsets(self, request, obj=None):
        if obj:
            user_field = ('user_display_link',)
        else:
            user_field = ('user',)

        return (
            ("Información del Pedido", { 'fields': ('id',) + user_field + ('fecha_pedido', 'actualizado', 'estado_pedido', 'metodo_pago', 'pagado', 'id_transaccion_pago', 'activo') }),
            ("Datos del Cliente (Snapshot)", { 'description': "Si seleccionas un 'Cliente (Usuario)' registrado, estos campos se llenarán automáticamente al guardar si están vacíos. Si no seleccionas un usuario (lo dejas en blanco), debes llenarlos manualmente.", 'fields': ('nombre_cliente', 'email_cliente', 'dni_cliente', 'telefono_contacto_envio') }),
            ("Dirección de Envío", { 'fields': ('direccion_envio', 'ciudad_envio', 'departamento_envio', 'pais_envio') }),
            ("Dirección de Facturación", { 'classes': ('collapse',), 'fields': ('usar_misma_direccion_facturacion', 'direccion_facturacion') }),
            ("Totales", { 'fields': ('subtotal', 'costo_envio', 'total_pedido') }),
            ("Observaciones", { 'fields': ('observaciones_cliente', 'observaciones_internas') }),
        )

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


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    # --- CAMBIO ---: Actualizamos todos los campos para que coincidan con el nuevo modelo.
    list_display = ('order_id_display', 'product_display', 'cantidad', 'precio_unitario_variante', 'get_costo_total')
    readonly_fields = ('order', 'variant', 'nombre_producto', 'precio_unitario_variante', 'precio_base_producto', 'proveedor_producto')
    search_fields = ('order__id__istartswith', 'variant__product__nombre', 'nombre_producto')
    list_filter = ('variant__product__categoria',)

    def order_id_display(self, obj):
        return obj.order.id_display
    order_id_display.short_description = "ID Pedido"

    def product_display(self, obj):
        return str(obj.variant) if obj.variant else obj.nombre_producto
    product_display.short_description = "Producto (Variante)"