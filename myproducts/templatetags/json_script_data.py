# myproducts/templatetags/json_script_data.py
import json
from django.template import Library
from django.utils.safestring import mark_safe
from django.core.serializers.json import DjangoJSONEncoder

register = Library()

@register.filter
def json_script_data(data, element_id):
    """
    Toma un QuerySet, lo convierte a una lista de diccionarios seguros
    y lo serializa a JSON para un script tag.
    """
    if not hasattr(data, '__iter__'):
        return ""
    
    # Convierte el QuerySet a una lista de diccionarios simples
    data_list = list(data.values('id', 'nombre')) # Asumimos 'nombre' como el campo principal
    json_data = json.dumps(data_list, cls=DjangoJSONEncoder)
    
    return mark_safe(f'<script id="{element_id}" type="application/json">{json_data}</script>')