from django.urls import path
from . import views # Asegúrate de que tus vistas de 'core' estén importadas
from django.views.generic import TemplateView

app_name = 'core'  # <--- ESTA LÍNEA ES CRUCIAL

urlpatterns = [
    path('', views.home_view, name='home'), # Tu vista para la página de inicio
    path('informacion/', TemplateView.as_view(template_name="core/about_us.html"), name='informacion'),
]