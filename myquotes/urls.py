# myquotes/urls.py
from django.urls import path
from . import views

app_name = 'myquotes'

urlpatterns = [
    path('<uuid:quote_id>/pdf/', views.generar_cotizacion_pdf, name='quote_pdf'),
]