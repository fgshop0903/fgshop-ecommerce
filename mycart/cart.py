# mycart/cart.py

from decimal import Decimal
from django.conf import settings
from django.db.models import Prefetch 
from myproducts.models import Product, ProductVariant, AttributeImage
from .forms import CartUpdateQuantityForm
from collections import defaultdict
from .models import Cart as DbCart, CartItem
import urllib.parse

class Cart:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        self.user = request.user
        
        cart_session = self.session.get(settings.CART_SESSION_ID)
        if not cart_session:
            cart_session = self.session[settings.CART_SESSION_ID] = {}
        self.cart_session = cart_session

    def add(self, product, variant, quantity=1, update_quantity=False):
        variant_id_str = str(variant.id)
        
        if self.user.is_authenticated:
            db_cart, _ = DbCart.objects.get_or_create(user=self.user)
            cart_item, created = CartItem.objects.get_or_create(
                cart=db_cart, 
                variant=variant,
                defaults={'quantity': quantity}
            )
            if not created:
                if update_quantity:
                    cart_item.quantity = quantity
                else:
                    cart_item.quantity += quantity
                
                if cart_item.quantity > variant.stock_disponible:
                    cart_item.quantity = variant.stock_disponible
                
                if cart_item.quantity <= 0:
                    cart_item.delete()
                else:
                    cart_item.save()
        else:
            if variant_id_str not in self.cart_session:
                self.cart_session[variant_id_str] = {'quantity': 0, 'price': str(variant.precio_variante), 'selected': True}
            
            if update_quantity:
                self.cart_session[variant_id_str]['quantity'] = quantity
            else:
                self.cart_session[variant_id_str]['quantity'] += quantity

            if self.cart_session[variant_id_str]['quantity'] <= 0:
                self.remove(variant_id_str)
            else:
                self.save()

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart_session
        self.session.modified = True

    def remove(self, variant_id):
        variant_id_str = str(variant_id)
        if self.user.is_authenticated:
            db_cart = DbCart.objects.filter(user=self.user).first()
            if db_cart:
                CartItem.objects.filter(cart=db_cart, variant_id=variant_id_str).delete()
        else:
            if variant_id_str in self.cart_session:
                del self.cart_session[variant_id_str]
                self.save()

    def clear(self):
        if self.user.is_authenticated:
            DbCart.objects.filter(user=self.user).delete()
        
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.save()

    def update_selection(self, variant_id, selected):
        variant_id_str = str(variant_id)
        
        if self.user.is_authenticated:
            db_cart = DbCart.objects.filter(user=self.user).first()
            if db_cart:
                CartItem.objects.filter(cart=db_cart, variant_id=variant_id_str).update(selected=selected)
                return True
        else:
            if variant_id_str in self.cart_session:
                self.cart_session[variant_id_str]['selected'] = selected
                self.save()
                return True
        return False

    def __iter__(self):
        if self.user.is_authenticated:
            try:
                # OPTIMIZAMOS LA CONSULTA DEL CARRITO
                db_cart = DbCart.objects.prefetch_related(
                    Prefetch(
                        'items',
                        queryset=CartItem.objects.select_related(
                            'variant__product__brand', 
                            'variant__product__supplier',
                            'variant__product__visual_attribute'
                        ).prefetch_related(
                            'variant__options__attribute',
                            'variant__product__attribute_images__attribute_value'
                        )
                    )
                ).get(user=self.user)
                
                for item in db_cart.items.all():
                    price = item.variant.precio_variante
                    discount = Decimal('0.00')
                    if item.variant.product.precio_base and item.variant.product.precio_base > price:
                        discount = (item.variant.product.precio_base - price) * item.quantity
                    
                    yield {
                        'variant': item.variant,
                        'quantity': item.quantity,
                        'price': price,
                        # --- ¡AQUÍ ESTÁ LA CORRECCIÓN! ---
                        'image_url': item.variant.get_visual_image_url(),
                        'selected': item.selected,
                        'subtotal': item.get_subtotal,
                        'discount': discount,
                        'update_quantity_form': CartUpdateQuantityForm(initial={'quantity': item.quantity, 'update': True}),
                        'is_unavailable': (not item.variant.activo or item.variant.stock_disponible < item.quantity)
                    }
            except DbCart.DoesNotExist:
                return
        else:
            variant_ids = self.cart_session.keys()
            # OPTIMIZAMOS LA CONSULTA PARA INVITADOS TAMBIÉN
            variants_in_db = ProductVariant.objects.filter(id__in=variant_ids).select_related(
                'product__brand', 'product__supplier', 'product__visual_attribute'
            ).prefetch_related(
                'options__attribute',
                'product__attribute_images__attribute_value'
            )
            
            variants_map = {str(v.id): v for v in variants_in_db}

            for variant_id_str, session_data in self.cart_session.items():
                variant_obj = variants_map.get(variant_id_str)
                if variant_obj:
                    price = Decimal(session_data['price'])
                    quantity = session_data['quantity']
                    discount = Decimal('0.00')
                    if variant_obj.product.precio_base and variant_obj.product.precio_base > price:
                        discount = (variant_obj.product.precio_base - price) * quantity
                    
                    yield {
                        'variant': variant_obj,
                        'quantity': quantity,
                        'price': price,
                        # --- ¡Y AQUÍ TAMBIÉN ESTÁ LA CORRECCIÓN! ---
                        'image_url': variant_obj.get_visual_image_url(),
                        'selected': session_data.get('selected', True),
                        'subtotal': price * quantity,
                        'discount': discount,
                        'update_quantity_form': CartUpdateQuantityForm(initial={'quantity': quantity, 'update': True}),
                        'is_unavailable': (not variant_obj.activo or variant_obj.stock_disponible < quantity)
                    }

    def get_selected_items(self):
        return [item for item in self if item['selected'] and not item.get('is_unavailable', False)]

    def get_total_price(self):
        return sum(item['price'] * item['quantity'] for item in self.get_selected_items())

    def get_total_discount(self):
        return sum(item.get('discount', Decimal('0.00')) for item in self.get_selected_items())
    
    def get_discounted_items_count(self):
        count = 0
        for item in self.get_selected_items():
            if item.get('discount', Decimal('0.00')) > 0:
                count += 1
        return count

    def __len__(self):
        if self.user.is_authenticated:
            db_cart = DbCart.objects.filter(user=self.user).first()
            return sum(item.quantity for item in db_cart.items.all()) if db_cart else 0
        else:
            return sum(item['quantity'] for item in self.cart_session.values())

    def get_selected_items_count(self):
        return sum(item['quantity'] for item in self.get_selected_items())

    def get_items_by_supplier(self):
        items_by_supplier = defaultdict(list)
        for item in self:
            supplier_name = item['variant'].product.supplier.nombre_empresa if item['variant'].product.supplier else "FG Shop"
            items_by_supplier[supplier_name].append(item)
        return dict(items_by_supplier)
    
    def get_variant_quantity(self, variant_id):
        variant_id_str = str(variant_id)
        if self.user.is_authenticated:
            db_cart = DbCart.objects.filter(user=self.user).first()
            if db_cart:
                item = db_cart.items.filter(variant_id=variant_id_str).first()
                return item.quantity if item else 0
            return 0
        else:
            if variant_id_str in self.cart_session:
                return self.cart_session[variant_id_str]['quantity']
            return 0
        
    def get_whatsapp_url(self, phone_number="938709302"):
        selected_items = self.get_selected_items()
        if not selected_items:
            return ""

        mensaje_items = []
        for item in selected_items:
            linea = (f"- {item['quantity']} x {item['variant'].product.nombre} "
                    f"({item['variant'].nombre_variante}) - S/ {item['price']:.2f} c/u")
            mensaje_items.append(linea)
        
        total = self.get_total_price()

        # Construir el mensaje final paso a paso para evitar errores de f-string
        mensaje_final = "¡Hola FG Shop! 👋\n\n"
        mensaje_final += "Quisiera confirmar mi pedido:\n\n"
        mensaje_final += '\n'.join(mensaje_items)
        mensaje_final += f"\n\n*Total: S/ {total:.2f}*\n\n"
        mensaje_final += "¡Quedo a la espera de las instrucciones para el pago!"
        
        mensaje_codificado = urllib.parse.quote(mensaje_final)
        
        return f"https://wa.me/{phone_number}?text={mensaje_codificado}"
    
    def has_selected_items(self):
        return bool(self.get_selected_items())