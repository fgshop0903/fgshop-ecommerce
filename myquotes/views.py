# myquotes/views.py
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.staticfiles.finders import find
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import Quote

def generar_cotizacion_pdf(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)

    if not request.user.is_staff:
        return HttpResponse("Acceso no autorizado", status=403)

    logo_path = find('core/img/logo_fgshop.png')

    context = {
        'quote': quote,
        'logo_path': logo_path,
    }
    
    template_path = 'myquotes/quote_pdf_template.html'
    html = get_template(template_path).render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cotizacion-{quote.numero_cotizacion}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Hubo un error al generar el PDF.')
        
    return response