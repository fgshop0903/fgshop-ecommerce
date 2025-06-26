from django.contrib import admin
from .models import Delivery

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = (
        'order_id_display', 'cliente_nombre_display', 'estado_entrega',
        'transportista', 'numero_seguimiento',
        'fecha_programada_envio', 'fecha_estimada_entrega_cliente', 'fecha_entrega_real_cliente'
    )
    list_filter = ('estado_entrega', 'transportista', 'fecha_programada_envio', 'fecha_estimada_entrega_cliente')
    search_fields = (
        'order__id__istartswith', # Buscar por inicio del UUID del pedido
        'order__nombre_cliente', 'order__user__username', 'order__user__email',
        'transportista', 'numero_seguimiento', 'entregado_por_persona'
    )
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'order_link')
    autocomplete_fields = ['order']
    fieldsets = (
        ("Información del Pedido Asociado", {
            'fields': ('order_link',)
        }),
        ("Estado y Programación", {
            'fields': ('estado_entrega', 'fecha_programada_envio', 'fecha_estimada_entrega_cliente', 'fecha_entrega_real_cliente')
        }),
        ("Información del Transportista", {
            'fields': ('transportista', 'entregado_por_persona', 'numero_seguimiento', 'url_seguimiento')
        }),
        ("Costos y Observaciones", {
            'fields': ('costo_real_envio', 'observaciones_envio')
        }),
        ("Timestamps", {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    raw_id_fields = ['order']
    autocomplete_fields = ['order']

    def get_fieldsets(self, request, obj=None):
        if obj: # Si estamos editando...
            order_field = ('order_link',)
        else: # Si estamos añadiendo...
            order_field = ('order',)

        return (
            ("Información del Pedido Asociado", {
                'fields': order_field
            }),
            ("Estado y Programación", {
                'fields': ('estado_entrega', 'fecha_programada_envio', 'fecha_estimada_entrega_cliente', 'fecha_entrega_real_cliente')
            }),
            ("Información del Transportista", {
                'fields': ('transportista', 'entregado_por_persona', 'numero_seguimiento', 'url_seguimiento')
            }),
            ("Costos y Observaciones", {
                'fields': ('costo_real_envio', 'observaciones_envio')
            }),
            ("Timestamps", {
                'fields': ('fecha_creacion', 'fecha_actualizacion'),
                'classes': ('collapse',)
            }),
        ) 

    def order_id_display(self, obj):
        return obj.order.id_display
    order_id_display.short_description = "ID Pedido"
    order_id_display.admin_order_field = 'order__id'

    def cliente_nombre_display(self, obj):
        return obj.order.nombre_cliente or (obj.order.user.get_full_name() if obj.order.user else "N/A")
    cliente_nombre_display.short_description = "Cliente"
    cliente_nombre_display.admin_order_field = 'order__nombre_cliente' # o user

    def order_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:myorders_order_change", args=[obj.order.id])
        return format_html('<a href="{}">Ver Pedido #{}</a>', link, obj.order.id_display)
    order_link.short_description = "Pedido"