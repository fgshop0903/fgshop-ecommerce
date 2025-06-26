from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import OrderItem

@receiver(post_save, sender=OrderItem)
def reducir_stock_al_crear_o_actualizar(sender, instance, created, **kwargs):
    """
    Esta señal se dispara DESPUÉS de que un OrderItem se guarda.
    Reduce el stock de la variante correspondiente.
    """
    # El 'instance' es el OrderItem que se acaba de guardar
    variante = instance.variant
    cantidad_pedida = instance.cantidad

    # Si la variante aún existe en el sistema...
    if variante:
        # 'created' es True si es la primera vez que se guarda este ítem
        if created:
            # Si es un ítem nuevo, simplemente restamos el stock
            variante.stock_disponible -= cantidad_pedida
            variante.save(update_fields=['stock_disponible'])
            print(f"NUEVO ÍTEM: Se restaron {cantidad_pedida} del stock de '{variante}'. Nuevo stock: {variante.stock_disponible}")
        else:
            # Si se está actualizando un ítem (ej. se cambió la cantidad)...
            # Necesitamos saber cuál era la cantidad ANTERIOR para ajustar correctamente.
            # Esta es una lógica más avanzada que podemos implementar después si la necesitas.
            # Por ahora, asumimos que la cantidad no se edita una vez creada.
            pass


@receiver(post_delete, sender=OrderItem)
def reponer_stock_al_eliminar(sender, instance, **kwargs):
    """
    Esta señal se dispara DESPUÉS de que un OrderItem se elimina.
    Devuelve el stock a la variante correspondiente.
    """
    # El 'instance' es el OrderItem que se acaba de borrar
    variante = instance.variant
    cantidad_a_reponer = instance.cantidad

    # Si la variante aún existe...
    if variante:
        # Sumamos la cantidad de vuelta al stock
        variante.stock_disponible += cantidad_a_reponer
        variante.save(update_fields=['stock_disponible'])
        print(f"ÍTEM ELIMINADO: Se repusieron {cantidad_a_reponer} al stock de '{variante}'. Nuevo stock: {variante.stock_disponible}")