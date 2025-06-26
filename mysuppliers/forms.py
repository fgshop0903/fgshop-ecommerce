from django import forms
from .models import Supplier

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'nombre_empresa', 'ruc', 'estado', 'tipo_proveedor',
            'nombre_contacto', 'telefono_contacto', 'correo_contacto', 'sitio_web',
            'direccion_fiscal', 'direccion_almacen',
            'terminos_pago', 'tiempo_entrega_promedio_a_fg', 'calificacion_interna',
            'observaciones_generales'
        ]
        widgets = {
            'direccion_fiscal': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'direccion_almacen': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'observaciones_generales': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'nombre_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '11 dígitos'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'tipo_proveedor': forms.Select(attrs={'class': 'form-select'}),
            'nombre_contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: +51987654321'}),
            'correo_contacto': forms.EmailInput(attrs={'class': 'form-control'}),
            'sitio_web': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://ejemplo.com'}),
            'terminos_pago': forms.TextInput(attrs={'class': 'form-control'}),
            'tiempo_entrega_promedio_a_fg': forms.TextInput(attrs={'class': 'form-control'}),
            'calificacion_interna': forms.Select(attrs={'class': 'form-select'}),
        }
        help_texts = {
            'ruc': 'Ingresar los 11 dígitos del RUC sin guiones ni espacios.',
            'calificacion_interna': 'Una calificación de 1 (malo) a 5 (excelente) sobre la fiabilidad y calidad del proveedor.',
        }

class SupplierImportForm(forms.Form):
    file = forms.FileField(
        label="Selecciona el archivo Excel de Proveedores (.xlsx)",
        help_text="El archivo debe tener las columnas: nombre_empresa, ruc, etc.",
        widget=forms.ClearableFileInput(attrs={'accept': '.xlsx'})
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file.name.endswith('.xlsx'):
            raise forms.ValidationError("El archivo debe tener la extensión .xlsx")
        return file