from django import forms
from .models import Product, Categoria, Attribute # Importa Attribute
from .models import AttributeValue
from itertools import product as cartesian_product
from django import forms


class ProductForm(forms.ModelForm):
    # Opcional: Si quieres un widget diferente para configurable_attributes
    # configurable_attributes = forms.ModelMultipleChoiceField(
    #     queryset=Attribute.objects.all(),
    #     widget=forms.CheckboxSelectMultiple,
    #     required=False, # O True si siempre deben seleccionarse atributos
    #     label="Atributos para Variantes"
    # )

    class Meta:
        model = Product
        fields = [
            'nombre',
            'slug',
            'categoria',
            'descripcion',
            'precio_base',
            'configurable_attributes',
            'activo',
            'destacado',
            # 'default_variant' usualmente se maneja en el admin o con lógica post-guardado,
            # ya que depende de que las variantes ya existan.
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dejar en blanco para autogenerar'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'precio_base': forms.NumberInput(attrs={'class': 'form-control'}),
            'imagen_principal': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'configurable_attributes': forms.SelectMultiple(attrs={'class': 'form-select form-select-lg', 'size': '5'}),
        }
        labels = {
            'nombre': 'Nombre del Producto',
            'slug': 'Slug (URL amigable)',
            'precio_base': 'Precio Base de Referencia (S/.)',
            'imagen_principal': 'Imagen Principal del Producto',
            'configurable_attributes': 'Atributos Configurables para Variantes',
        }
        help_texts = {
            'slug': 'Dejar en blanco para autogenerar. Usar solo letras, números, guiones o guiones bajos.',
            'precio_base': 'Precio base si el producto no tiene variantes o como referencia general. Las variantes tendrán su propio precio.',
            'configurable_attributes': 'Selecciona los atributos (ej. Talla, Color) que este producto utilizará para definir sus diferentes variantes.',
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        nombre = self.cleaned_data.get('nombre')

        # Generar slug a partir del nombre si el slug está vacío y el nombre existe
        if not slug and nombre:
            from django.utils.text import slugify # Mover importación aquí o al inicio del archivo
            slug = slugify(nombre)

        if slug:
            qs = Product.objects.filter(slug=slug)
            if self.instance and self.instance.pk: # Editando
                qs = qs.exclude(pk=self.instance.pk)
            
            # Si después de generar/usar el slug, este todavía existe, intentar añadir un contador
            original_slug = slug
            counter = 1
            while qs.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            # Si el slug final (después de añadir contador) sigue existiendo y no es el slug original del objeto (si estamos editando)
            # esto indicaría un problema raro, pero la lógica anterior debería prevenirlo.
            # Aquí, una validación final de unicidad si el slug fue modificado por el contador:
            if slug != original_slug and Product.objects.filter(slug=slug).exclude(pk=self.instance.pk if self.instance and self.instance.pk else None).exists():
                 raise forms.ValidationError("Este slug ya está en uso o el generado automáticamente ya existe. Intenta un nombre ligeramente diferente.")

        return slug

    def clean(self):
        cleaned_data = super().clean()
        # Aquí puedes poner validaciones que involucren múltiples campos del ProductForm
        # Por ejemplo:
        # if cleaned_data.get('destacado') and not cleaned_data.get('activo'):
        #     self.add_error('destacado', 'Un producto no puede ser destacado si no está activo.')
        return cleaned_data
    
class VariantCombinationForm(forms.Form):
    """
    Formulario dinámico para seleccionar combinaciones de variantes a crear.
    """
    # Usamos un campo que puede tener múltiples opciones seleccionadas (checkboxes)
    combinations = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        required=True, # Forzamos a que se seleccione al menos una
        label="Selecciona las combinaciones a crear:"
    )

    def __init__(self, product, *args, **kwargs):
        """
        El 'truco' está en el __init__. Aquí es donde dinámicamente
        poblamos los 'choices' de nuestro campo 'combinations'.
        """
        super().__init__(*args, **kwargs)
        self.product = product
        
        # Le pasamos las opciones calculadas a nuestro campo
        self.fields['combinations'].choices = self._get_possible_combinations()
        self.fields['combinations'].error_messages = {
            'required': 'Debes seleccionar al menos una combinación para continuar.'
        }

    def _get_possible_combinations(self):
 
        configurable_attributes = self.product.configurable_attributes.all()

        if not configurable_attributes.exists():
            return []
        
        value_lists = []
        for attr in configurable_attributes:
            values = list(AttributeValue.objects.filter(attribute=attr))
            if not values:
                return []
            value_lists.append(values)

        all_combinations = list(cartesian_product(*value_lists))
        
        choices = []
        for combo_tuple in all_combinations:
            label = " / ".join(v.value for v in combo_tuple)
            value = "_".join(str(v.id) for v in combo_tuple)
            choices.append((value, label))
            
        return choices

    def get_selected_attribute_value_lists(self):
        """
        Una vez el formulario es válido, esta función convierte las cadenas
        "id1_id2_..." de nuevo en listas de objetos AttributeValue.
        """
        cleaned_data = self.cleaned_data.get('combinations', [])
        
        final_lists = []
        for combo_string in cleaned_data:
            ids = [int(id_str) for id_str in combo_string.split('_')]
            # Hacemos una consulta a la BD para obtener los objetos AttributeValue
            values = list(AttributeValue.objects.filter(pk__in=ids))
            final_lists.append(values)
            
        return final_lists
    
class ProductImportForm(forms.Form):
    file = forms.FileField(
        label="Selecciona el archivo Excel (.xlsx)",
        help_text="El archivo debe seguir la plantilla definida.",
        widget=forms.ClearableFileInput(attrs={'accept': '.xlsx'})
    )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file.name.endswith('.xlsx'):
            raise forms.ValidationError("El archivo debe tener la extensión .xlsx")
        return file