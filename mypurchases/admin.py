from django.contrib import admin
from .models import (
    PurchaseOrder, 
    PurchaseOrderItem, 
    PurchasePayment, 
    PurchaseDelivery, 
    PurchaseDeliveryItem
)

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    autocomplete_fields = ['variant']
    fields = ('variant', 'quantity', 'unit_cost', 'display_subtotal', 'received_quantity')
    readonly_fields = ('display_subtotal', 'received_quantity')

    def display_subtotal(self, obj):
        return obj.subtotal
    display_subtotal.short_description = "Subtotal"

class PurchasePaymentInline(admin.TabularInline):
    model = PurchasePayment
    extra = 0
    fields = ('payment_date', 'amount', 'payment_method', 'reference_code', 'receipt_file', 'notes')

class PurchaseDeliveryItemInline(admin.TabularInline):
    model = PurchaseDeliveryItem
    extra = 1
    autocomplete_fields = ['order_item']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'order_date', 'status', 'total_amount', 'payment_status')
    list_filter = ('status', 'payment_status', 'supplier', 'order_date', 'is_installment')
    search_fields = ('id', 'supplier__nombre_empresa', 'invoice_number')
    date_hierarchy = 'order_date'
    inlines = [PurchaseOrderItemInline, PurchasePaymentInline]
    readonly_fields = ('subtotal_amount', 'total_amount', 'created_by', 'created_at', 'updated_at')
    fieldsets = (
        ('Información Principal', {
            'fields': ('supplier', 'order_date', 'status', 'expected_delivery_date')
        }),
        ('Detalles Financieros y Factura', {
            'fields': (
                ('invoice_number', 'invoice_date'),
                ('payment_status', 'payment_due_date'),
                ('subtotal_amount', 'shipping_cost', 'total_amount'),
                'document_file'
            )
        }),
        ("Configuración de Compra a Cuotas", {
            'classes': ('collapse',),
            'fields': ('is_installment', 'installments_count', 'installment_amount')
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
        ('Notas Adicionales', {
            'fields': ('notes',),
        }),
    )

    # --- ¡LÓGICA SIMPLIFICADA AQUÍ! ---
    def save_model(self, request, obj, form, change):
        if not change: # Si es un objeto nuevo
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        obj.calculate_totals() # Siempre recalcular al guardar la orden

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        # Después de guardar los ítems, le pedimos a la orden que se recalcule
        form.instance.calculate_totals()

@admin.register(PurchaseDelivery)
class PurchaseDeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'purchase_order', 'delivery_date', 'received_by')
    list_filter = ('delivery_date',)
    search_fields = ('purchase_order__id', 'tracking_number')
    autocomplete_fields = ['purchase_order', 'received_by']
    inlines = [PurchaseDeliveryItemInline]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.received_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PurchasePayment)
class PurchasePaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'purchase_order', 'payment_date', 'amount', 'payment_method')
    autocomplete_fields = ['purchase_order']

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'purchase_order', 'variant', 'quantity', 'unit_cost')
    autocomplete_fields = ['purchase_order', 'variant']
    search_fields = ('variant__product__nombre', 'variant__nombre_variante')