"""
URL configuration for mystore project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('productos/', include('myproducts.urls', namespace='myproducts')),
    path('clientes/', include('mycustomers.urls', namespace='mycustomers')),
    path('pedidos/', include('mysales.urls', namespace='mysales')),
    path('cotizaciones/', include('myquotes.urls', namespace='myquotes')),
    path('entregas/', include('mydeliveries.urls', namespace='mydeliveries')),
    path('proveedores/', include('mysuppliers.urls', namespace='mysuppliers')),
    path('carrito/', include('mycart.urls', namespace='mycart')),
    path('accounts/', include('allauth.urls')),
] 

# Agrega rutas para servir archivos multimedia (como imágenes) solo si MEDIA_URL y MEDIA_ROOT están definidos
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

