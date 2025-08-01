from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Delivery
from mysales.models import Order 

@receiver(post_save, sender=Delivery)
def actualizar_estado_del_pedido(sender, instance, **kwargs):
    """
    Esta señal se dispara DESPUÉS de que un registro de Delivery se guarda.
    Su trabajo es actualizar el estado del Pedido (Order) principal.
    """
    delivery = instance
    order = delivery.order

    nuevo_estado_pedido = None

    # Mapeamos el estado del envío al estado del pedido
    if delivery.estado_entrega == 'ENTREGADO':
        nuevo_estado_pedido = 'ENTREGADO'
    elif delivery.estado_entrega == 'EN_RUTA_CLIENTE':
        nuevo_estado_pedido = 'EN_CAMINO_CLIENTE'
    # Puedes añadir más reglas aquí, por ejemplo:
    # elif delivery.estado_entrega == 'PREPARANDO_ENVIO_CLIENTE':
    #     nuevo_estado_pedido = 'LISTO_PARA_ENVIO'

    # Si encontramos un nuevo estado para el pedido y es diferente al actual...
    if nuevo_estado_pedido and order.estado_pedido != nuevo_estado_pedido:
        order.estado_pedido = nuevo_estado_pedido
        
        # Si se entrega, lo marcamos como pagado (útil para contraentrega)
        if nuevo_estado_pedido == 'ENTREGADO' and not order.pagado:
            order.pagado = True
            order.save(update_fields=['estado_pedido', 'pagado'])
        else:
            order.save(update_fields=['estado_pedido'])
        
        print(f"SEÑAL: El estado del Pedido #{order.id_display} se actualizó a '{nuevo_estado_pedido}'")