# En algun_app/context_processors.py
from myproducts.models import Categoria

def categories_for_menu(request):
    main_categories = Categoria.objects.filter(padre__isnull=True).prefetch_related(
        'subcategorias',                      # Nivel 2 (Hijas de Nivel 1)
        'subcategorias__subcategorias'        # Nivel 3 (Nietas de Nivel 1, o Hijas de Nivel 2)
    ).order_by('nombre')
    return {'main_categories_for_menu': main_categories}