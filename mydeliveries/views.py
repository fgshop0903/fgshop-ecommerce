from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from .models import Delivery
from myorders.models import Order # Para la vista de seguimiento
from .forms import DeliveryForm, PublicTrackingForm
import uuid # Para manejar el UUID del pedido

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class DeliveryListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Delivery
    template_name = 'mydeliveries/delivery_list.html'
    context_object_name = 'deliveries'
    paginate_by = 20

    def get_queryset(self):
        return Delivery.objects.select_related('order', 'order__user').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Gestión de Envíos"
        return context

class DeliveryCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    model = Delivery
    form_class = DeliveryForm
    template_name = 'mydeliveries/delivery_form.html'
    success_url = reverse_lazy('mydeliveries:delivery_list')

    def form_valid(self, form):
        messages.success(self.request, "Información de envío creada exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Registrar Nuevo Envío"
        context['nombre_boton'] = "Guardar Envío"
        return context

class DeliveryUpdateView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    model = Delivery
    form_class = DeliveryForm
    template_name = 'mydeliveries/delivery_form.html'
    success_url = reverse_lazy('mydeliveries:delivery_list')

    def form_valid(self, form):
        messages.success(self.request, "Información de envío actualizada exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f"Actualizar Envío para Pedido #{self.object.order.id_display}"
        context['nombre_boton'] = "Actualizar Envío"
        return context

class DeliveryDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = Delivery
    template_name = 'mydeliveries/delivery_detail.html' # Crear esta plantilla
    context_object_name = 'delivery'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = f"Detalle de Envío para Pedido #{self.object.order.id_display}"
        return context


# Vista pública para seguimiento
def public_order_tracking_view(request):
    delivery = None
    order = None
    error_message = None
    form = PublicTrackingForm(request.GET or None)

    if form.is_valid():
        order_id_short = form.cleaned_data['order_id_display'].upper()
        # Buscar pedidos cuyo UUID comience con el ID corto
        # Esto es una simplificación. En producción, podrías necesitar un campo 'short_id' indexado en Order.
        possible_orders = Order.objects.filter(id__istartswith=order_id_short.replace("-", ""))

        if not possible_orders.exists():
            error_message = "No se encontró ningún pedido con ese ID."
        elif possible_orders.count() > 1:
            # Esto es poco probable con UUIDs, pero si usaras IDs cortos más simples podría pasar.
            error_message = "Se encontraron múltiples pedidos. Por favor, contacta a soporte."
        else:
            order = possible_orders.first()
            try:
                delivery = order.delivery_info # Usando el related_name
            except Delivery.DoesNotExist:
                # El pedido existe pero no tiene información de envío aún
                pass # 'delivery' seguirá siendo None, se maneja en la plantilla
            # Opcional: Verificar email/DNI si se incluye en el formulario
            # email_o_dni = form.cleaned_data.get('email_o_dni')
            # if email_o_dni and order:
            #     if not (order.email_cliente == email_o_dni or (order.user and order.user.email == email_o_dni) or order.dni_cliente == email_o_dni):
            #         order = None # No coincide la verificación
            #         delivery = None
            #         error_message = "La información de verificación no coincide con el pedido."

    context = {
        'form': form,
        'order': order,
        'delivery': delivery,
        'error_message': error_message,
        'titulo_pagina': "Seguimiento de Pedido"
    }
    return render(request, 'mydeliveries/public_tracking.html', context)