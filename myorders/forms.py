from django import forms
from .models import Order # OrderItem se crea programáticamente

class CheckoutForm(forms.ModelForm):
    # Campos que el usuario llenaría o confirmaría en el checkout
    # El 'user' se asigna desde request.user
    # El 'email_cliente', 'nombre_cliente' se pueden prellenar desde el user
    email_cliente = forms.EmailField(label="Correo electrónico de contacto")
    nombre_cliente = forms.CharField(label="Nombre completo para el envío")
    dni_cliente = forms.CharField(label="DNI/Documento para el envío", max_length=20, required=False)
    telefono_contacto_envio = forms.CharField(label="Teléfono de contacto", max_length=20)

    direccion_envio = forms.CharField(label="Dirección", widget=forms.Textarea(attrs={'rows': 3}))
    ciudad_envio = forms.CharField(label="Ciudad")
    departamento_envio = forms.CharField(label="Departamento/Región")
    # pais_envio ya tiene default

    observaciones_cliente = forms.CharField(
        label="Notas adicionales para tu pedido (opcional)",
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False
    )
    # El método de pago se seleccionaría, y los totales se calculan
    # metodo_pago = forms.ChoiceField(choices=METODO_PAGO_CHOICES, widget=forms.RadioSelect) # Ejemplo

    class Meta:
        model = Order
        fields = [
            'email_cliente', 'nombre_cliente', 'dni_cliente', 'telefono_contacto_envio',
            'direccion_envio', 'ciudad_envio', 'departamento_envio', 'pais_envio',
            'observaciones_cliente',
            # 'usar_misma_direccion_facturacion', 'direccion_facturacion', ... (si es necesario)
            # 'metodo_pago'
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Extraer el usuario si se pasa
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            self.fields['email_cliente'].initial = user.email
            self.fields['nombre_cliente'].initial = user.get_full_name()
            if hasattr(user, 'customerprofile'):
                self.fields['dni_cliente'].initial = user.customerprofile.DNI
                self.fields['telefono_contacto_envio'].initial = user.customerprofile.telefono
                # Podrías prellenar la dirección si está en el perfil
                # self.fields['direccion_envio'].initial = user.customerprofile.direccion