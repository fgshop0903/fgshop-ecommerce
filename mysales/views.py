from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Order, OrderItem
from django.http import JsonResponse
from myproducts.models import ProductVariant
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from decimal import Decimal
from django.contrib.staticfiles.finders import find
from io import BytesIO  
# from .forms import CheckoutForm # Si implementas el checkout aquí
# from cart.cart import Cart # Asumiendo que tienes una app 'cart'

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class OrderHistoryView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'mysales/order_list.html'
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
    template_name = 'mysales/order_detail.html'
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
        context['titulo_pagina'] = f"Detalle del Pedido N° {self.object.id_display}"
        return context

# --- Vistas para Administradores (Staff) ---

class OrderAdminListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Order
    template_name = 'mysales/order_list.html'
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

def generate_invoice_pdf(request, order_id):
    """
    Toma una orden, la renderiza en una plantilla HTML y devuelve un PDF.
    """
    try:
        order = get_object_or_404(Order, id=order_id)
        # El usuario solo puede descargar sus propias facturas, a menos que sea staff
        if not request.user.is_staff and order.user != request.user:
            return HttpResponse("No autorizado", status=403)
    except Order.DoesNotExist:
        return HttpResponse("Orden no encontrada", status=404)

    # Cálculo de IGV (asumiendo que tus precios lo incluyen)
    # Tasa de IGV en Perú es 18% -> 1.18
    IGV_RATE = Decimal('1.18')
    total_pedido = Decimal(order.total_pedido)
    
    subtotal_sin_igv = total_pedido / IGV_RATE
    igv_calculado = total_pedido - subtotal_sin_igv

    template_path = 'mysales/invoice_pdf_template.html'
    context = {
        'order': order,
        'subtotal_sin_igv': subtotal_sin_igv,
        'igv_calculado': igv_calculado,
    }

    # Crear una respuesta HTTP con el tipo de contenido PDF
    response = HttpResponse(content_type='application/pdf')
    # Esto hará que se descargue con un nombre de archivo específico
    response['Content-Disposition'] = f'attachment; filename="comprobante_{order.id_display}.pdf"'
    
    # Renderizar la plantilla HTML
    template = get_template(template_path)
    html = template.render(context)

    # Crear el PDF
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    
    # Si hay un error, mostrarlo
    if pisa_status.err:
       return HttpResponse('Hubo un error al generar el PDF <pre>' + html + '</pre>')
    return response

def generar_nota_venta_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if not request.user.is_staff and order.user != request.user:
        return HttpResponse("No autorizado", status=403)

    # --- INICIO DE LA MODIFICACIÓN ---
    # 1. Le pedimos a Django que encuentre la ruta ABSOLUTA del logo.
    #    La ruta que le pasamos es relativa a CUALQUIER carpeta 'static'.
    #    Basado en tu captura, el logo se llama 'logo_fgshop.png'.
    logo_path = find('core/img/logo_fgshop.png')

    # 2. Creamos el contexto. Si 'find' no encontró el logo, logo_path será None.
    context = {
        'order': order,
        'logo_path': logo_path,
    }
    # --- FIN DE LA MODIFICACIÓN ---
    
    template_path = 'mysales/nota_venta_pdf_template.html'
    html = get_template(template_path).render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="nota-de-venta-{order.id_display}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Hubo un error al generar el PDF <pre>' + html + '</pre>')
        
    return response