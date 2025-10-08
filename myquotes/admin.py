# myquotes/admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Quote, QuoteItem

class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 1
    raw_id_fields = ('variant',)
    fields = ('variant', 'descripcion', 'cantidad', 'precio_unitario', 'get_subtotal_display')
    readonly_fields = ('get_subtotal_display',)

    def get_subtotal_display(self, obj):
        return f"S/ {obj.get_subtotal():.2f}"
    get_subtotal_display.short_description = "Subtotal (Sin IGV)"

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('numero_cotizacion', 'razon_social', 'fecha_emision', 'fecha_validez', 'total', 'estado')
    list_filter = ('estado', 'fecha_emision', 'fecha_validez')
    search_fields = ('numero_cotizacion', 'razon_social', 'ruc')
    inlines = [QuoteItemInline]
    
    # --- ¡CAMBIO #1: AÑADIMOS 'fecha_emision' A LOS CAMPOS DE SOLO LECTURA! ---
    readonly_fields = ('numero_cotizacion', 'fecha_emision', 'subtotal', 'igv', 'total', 'descargar_pdf_link')

    fieldsets = (
        ('Información del Cliente', {
            'fields': ('razon_social', 'ruc', 'direccion_cliente', 'atencion_a', ('email_cliente', 'telefono_cliente'))
        }),
        ('Detalles de la Cotización', {
            # --- ¡CAMBIO #2: QUITAMOS 'fecha_emision' DE LA TUPLA EDITABLE... ---
            #     ...Y LA PONEMOS JUNTO A LOS OTROS CAMPOS DE SOLO LECTURA!
            'fields': ('numero_cotizacion', 'estado', 'fecha_emision', 'fecha_validez', 'descargar_pdf_link')
        }),
        ('Totales Calculados', {
            'fields': ('subtotal', 'igv', 'total'),
            'classes': ('collapse',)
        }),
        ('Contenido del PDF', {
            'fields': ('terminos_y_condiciones', 'observaciones')
        }),
    )

    def descargar_pdf_link(self, obj):
        if obj.pk:
            url = reverse('myquotes:quote_pdf', args=[obj.id])
            return format_html('<a href="{}" class="button" target="_blank">Generar y Descargar PDF</a>', url)
        return "Guarde la cotización primero para generar el PDF."
    descargar_pdf_link.short_description = 'Documento PDF'

    def save_model(self, request, obj, form, change):
        if not obj.creado_por_id:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
    
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.calcular_totales()