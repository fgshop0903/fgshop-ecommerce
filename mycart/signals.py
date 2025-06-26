# mycart/signals.py

from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from .models import Cart, CartItem, ProductVariant

@receiver(user_logged_in)
def transfer_session_cart_to_db(sender, request, user, **kwargs):
    """
    Cuando un usuario inicia sesión, transfiere los items del carrito de sesión
    directamente a su carrito en la base de datos.
    """
    # Accedemos al diccionario del carrito de sesión directamente
    session_cart_data = request.session.get(settings.CART_SESSION_ID)

    if session_cart_data:
        # Obtiene o crea el carrito de base de datos para el usuario
        db_cart, _ = Cart.objects.get_or_create(user=user)

        # Para eficiencia, obtenemos todas las variantes de una vez
        variant_ids = session_cart_data.keys()
        variants_in_session = ProductVariant.objects.filter(id__in=variant_ids)
        variants_map = {str(v.id): v for v in variants_in_session}

        for variant_id, item_data in session_cart_data.items():
            variant = variants_map.get(variant_id)
            if not variant:
                continue # Si la variante ya no existe, la saltamos

            quantity_in_session = item_data.get('quantity', 0)
            if quantity_in_session <= 0:
                continue

            # Intenta obtener el item en el carrito de la BD
            cart_item, created = CartItem.objects.get_or_create(
                cart=db_cart,
                variant=variant,
                defaults={'quantity': quantity_in_session}
            )

            # Si el item ya existía, suma las cantidades
            if not created:
                cart_item.quantity += quantity_in_session
                # Asegurarse de no exceder el stock
                if cart_item.quantity > variant.stock_disponible:
                    cart_item.quantity = variant.stock_disponible
                cart_item.save()
        
        # Limpia el carrito de sesión después de la transferencia
        del request.session[settings.CART_SESSION_ID]
        request.session.modified = True