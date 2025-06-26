from django.db import models
from django.conf import settings
from myproducts.models import ProductVariant

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)

    selected = models.BooleanField(default=True) 

    class Meta:
        unique_together = ('cart', 'variant')

    def __str__(self):
        return f"{self.quantity} x {self.variant}"

    @property
    def get_subtotal(self):
        return self.variant.precio_variante * self.quantity

