from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Order, OrderItem
from django.http import JsonResponse
from myproducts.models import ProductVariant
# from .forms import CheckoutForm # Si implementas el checkout aquí
# from cart.cart import Cart # Asumiendo que tienes una app 'cart'

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class OrderHistoryView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'myorders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        # El usuario solo ve sus propios pedidos
        return Order.objects.filter(user=self.request.user).order_by('-fecha_pedido')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Mis Pedidos"
        context['es_admin_view'] = False
        return context

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'myorders/order_detail.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id' # Para usar UUID como pk

    def get_queryset(self):
        # El usuario solo puede ver detalles de sus propios pedidos
        # A menos que sea staff, en cuyo caso puede ver cualquiera (se maneja en get_object o mixin)
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f"Detalle del Pedido #{self.object.id_display}"
        return context

# --- Vistas para Administradores (Staff) ---

class OrderAdminListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Order
    template_name = 'myorders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        return Order.objects.all().order_by('-fecha_pedido')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Gestión de Pedidos"
        context['es_admin_view'] = True
        return context
    
def get_variant_details(request, variant_id):
    """
    Esta es una vista tipo API que devuelve los detalles de una variante
    en formato JSON para que nuestro JavaScript los pueda usar.
    """
    try:
        variant = ProductVariant.objects.select_related(
            'product__supplier'
        ).get(pk=variant_id)
        
        data = {
            'nombre_producto': str(variant),
            'precio_unitario': variant.precio_variante,
            'origen_producto_item': variant.product.supplier.nombre_empresa if variant.product.supplier else '',
        }
        return JsonResponse(data)
    
    except ProductVariant.DoesNotExist:
        return JsonResponse({'error': 'Variante no encontrada'}, status=404)
