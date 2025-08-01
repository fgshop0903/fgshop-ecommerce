# mypurchases/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import F

from .models import PurchaseDeliveryItem, PurchaseOrderItem, PurchaseOrder

@receiver(post_save, sender=PurchaseDeliveryItem)
@transaction.atomic
def update_stock_on_delivery(sender, instance, created, **kwargs):
    """
    Esta señal se activa después de guardar un PurchaseDeliveryItem.
    Su trabajo es actualizar el stock del producto y el estado de la orden.
    """
    if not created:
        # Por ahora, solo actuaremos en la creación para evitar duplicados si se edita.
        # En el futuro se puede añadir lógica para manejar ediciones.
        return

    order_item = instance.order_item
    variant = order_item.variant
    quantity_received = instance.quantity_received

    # 1. Actualizar el stock del producto (ProductVariant)
    # Usamos F() para evitar problemas de concurrencia (race conditions)
    variant.stock_disponible = F('stock_disponible') + quantity_received
    variant.save(update_fields=['stock_disponible'])
    
    # 2. Actualizar la cantidad recibida en el ítem de la orden
    order_item.received_quantity = F('received_quantity') + quantity_received
    order_item.save(update_fields=['received_quantity'])

    # 3. Actualizar el estado del ítem y de la orden completa
    # Necesitamos recargar el objeto desde la BD para obtener el valor actualizado por F()
    order_item.refresh_from_db()

    if order_item.received_quantity >= order_item.quantity:
        order_item.status = PurchaseOrderItem.Status.RECEIVED
    order_item.save(update_fields=['status'])
    
    # Ahora, revisamos el estado de la orden de compra completa
    purchase_order = order_item.purchase_order
    
    # Si todavía hay ítems pendientes, la orden está parcialmente entregada
    if purchase_order.items.filter(status=PurchaseOrderItem.Status.PENDING).exists():
        purchase_order.status = PurchaseOrder.Status.PARTIALLY_DELIVERED
    else:
        # Si no hay ítems pendientes, la orden está totalmente entregada
        purchase_order.status = PurchaseOrder.Status.FULLY_DELIVERED
    
    purchase_order.save(update_fields=['status'])