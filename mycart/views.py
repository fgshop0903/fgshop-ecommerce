# mycart/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from myproducts.models import Product, ProductVariant
from .cart import Cart
from .forms import CartAddProductForm, CartUpdateQuantityForm
import urllib.parse


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)

    if form.is_valid():
        cd = form.cleaned_data
        variant = get_object_or_404(ProductVariant, id=cd['variant_id'])
        current_quantity_in_cart = cart.get_variant_quantity(cd['variant_id'])
        total_desired_quantity = current_quantity_in_cart + cd['quantity']

        if total_desired_quantity > variant.stock_disponible:
            available_to_add = variant.stock_disponible - current_quantity_in_cart
            error_message = f"No puedes añadir esa cantidad. Solo puedes añadir {available_to_add} más." if available_to_add > 0 else "Ya tienes la máxima cantidad de este producto en tu carrito."
            messages.warning(request, error_message)
        else:
            cart.add(product=product, variant=variant, quantity=cd['quantity'], update_quantity=cd.get('update', False))
            messages.success(request, f"'{variant.product.nombre} ({variant.nombre_variante})' se añadió a tu carrito.")
    else:
        messages.error(request, "Hubo un error al añadir el producto.")

    return redirect(request.META.get('HTTP_REFERER', 'myproducts:product_list'))


# --- VISTA PARA ACTUALIZAR CANTIDAD (VÍA AJAX) ---
@require_POST
def cart_update(request, variant_id):
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    form = CartUpdateQuantityForm(request.POST)

    if form.is_valid():
        cd = form.cleaned_data
        quantity = cd['quantity']
        if quantity > variant.stock_disponible:
            return JsonResponse({'error': f'Solo quedan {variant.stock_disponible} unidades.'}, status=400)
        
        cart.add(product=variant.product, variant=variant, quantity=quantity, update_quantity=True)
        
        summary_html = render_to_string('mycart/partials/order_summary.html', {'cart': cart}, request=request)
        return JsonResponse({'success': True, 'summary_html': summary_html, 'whatsapp_url': cart.get_whatsapp_url(), 'has_selected_items': cart.has_selected_items()})
    
    return JsonResponse({'error': 'Cantidad inválida.'}, status=400)

# --- VISTA PARA CAMBIAR LA SELECCIÓN DE UN ITEM (VÍA AJAX) ---
@require_POST
def cart_toggle_selection(request, variant_id):
    cart = Cart(request)
    selected = request.POST.get('selected') == 'true'
    
    if cart.update_selection(variant_id, selected):
        summary_html = render_to_string('mycart/partials/order_summary.html', {'cart': cart}, request=request)
        return JsonResponse({'success': True, 'summary_html': summary_html, 'whatsapp_url': cart.get_whatsapp_url(), 'has_selected_items': cart.has_selected_items()})
        
    return JsonResponse({'success': False}, status=400)


# --- VISTA PARA ELIMINAR UN ITEM ---
def cart_remove(request, variant_id):
    cart = Cart(request)
    cart.remove(variant_id) # La lógica de mensajes ya está en la clase o se puede simplificar
    messages.success(request, "Producto eliminado del carrito.")
    return redirect('mycart:cart_detail')


# --- VISTA PARA VACIAR EL CARRITO ---
def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    messages.success(request, "Tu carrito ha sido vaciado exitosamente.")
    return redirect('mycart:cart_detail')


@require_POST
def cart_bulk_toggle_selection(request):
    cart = Cart(request)
    variant_ids = request.POST.getlist('variant_ids[]')
    selected = request.POST.get('selected') == 'true'
    
    for variant_id in variant_ids:
        cart.update_selection(variant_id, selected)

    summary_html = render_to_string('mycart/partials/order_summary.html', {'cart': cart}, request=request)
    return JsonResponse({'success': True, 'summary_html': summary_html, 'whatsapp_url': cart.get_whatsapp_url(),'has_selected_items': cart.has_selected_items()})

def cart_detail(request):
    cart = Cart(request)
    context = {
        'cart': cart,
        'titulo_pagina': "Mi Carrito de Compras",
        'whatsapp_url': cart.get_whatsapp_url(),
    }
    return render(request, 'mycart/cart_detail.html', context)