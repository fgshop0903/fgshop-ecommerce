# mydeliveries/forms.py
from django import forms
from .models import Delivery # Solo necesitas importar el modelo en sí

class DeliveryForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = [
            'order', 'estado_entrega', # Django tomará los CHOICES de Delivery.estado_entrega
            'fecha_programada_envio', 'fecha_estimada_entrega_cliente', 'fecha_entrega_real_cliente',
            'transportista', # Django tomará los CHOICES de Delivery.transportista
            'entregado_por_persona', 'numero_seguimiento', 'url_seguimiento',
            'costo_real_envio', 'observaciones_envio'
        ]
        widgets = {
            'fecha_programada_envio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_estimada_entrega_cliente': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_entrega_real_cliente': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observaciones_envio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            # No es necesario especificar 'choices' para 'transportista' y 'estado_entrega' aquí
            # si son CharFields con choices en el modelo y usas ModelForm.
            'transportista': forms.Select(attrs={'class': 'form-select'}),
            'estado_entrega': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.Select(attrs={'class': 'form-select'}),
            'numero_seguimiento': forms.TextInput(attrs={'class': 'form-control'}),
            'url_seguimiento': forms.URLInput(attrs={'class': 'form-control'}),
            'entregado_por_persona': forms.TextInput(attrs={'class': 'form-control'}),
            'costo_real_envio': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'fecha_programada_envio': 'Fecha Programada de Envío/Recojo',
            'fecha_estimada_entrega_cliente': 'Fecha Estimada de Entrega al Cliente',
            'fecha_entrega_real_cliente': 'Fecha de Entrega Real al Cliente',
            'entregado_por_persona': 'Persona/Repartidor que entrega (si aplica)',
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_programada = cleaned_data.get("fecha_programada_envio")
        fecha_entrega_real = cleaned_data.get("fecha_entrega_real_cliente")

        if fecha_programada and fecha_entrega_real:
            if fecha_entrega_real < fecha_programada:
                self.add_error('fecha_entrega_real_cliente', "La fecha de entrega real no puede ser anterior a la fecha programada de envío.")
        return cleaned_data

class PublicTrackingForm(forms.Form):
    order_id_display = forms.CharField(
        label="ID de Pedido (Ej: #ABC123EF)",
        max_length=10,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: ABC123EF'})
    )