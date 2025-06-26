from django import forms

PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)] # Cantidad de 1 a 20

class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1, widget=forms.HiddenInput())
    variant_id = forms.IntegerField(widget=forms.HiddenInput())
    update = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput())

class CartUpdateQuantityForm(forms.Form):
    quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm text-center', 'style': 'width: 60px;'}),
        label="",
        min_value=1
    )
    update = forms.BooleanField(required=False, initial=True, widget=forms.HiddenInput) # Siempre es update aquí