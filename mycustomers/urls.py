from django.urls import path, include
from . import views

app_name = 'mycustomers'

urlpatterns = [
    
    # Gestión de Perfil de Usuario
    path('perfil/', views.CustomerProfileDetailView.as_view(), name='profile_detail_self'), # Ver perfil propio
    path('perfil/editar/', views.CustomerProfileUpdateView.as_view(), name='profile_update'),

    # Rutas de django.contrib.auth para reseteo de contraseña, etc.
    # Es mejor ponerlas en el urls.py principal del proyecto, pero aquí como ejemplo.
    # path('auth/', include('django.contrib.auth.urls')),
    # Si las pones aquí, las plantillas deben estar en mycustomers/registration/

    # Vistas para Administradores (Staff)
    path('admin/listado/', views.CustomerListView.as_view(), name='customer_list_admin'),
    path('admin/perfil/<str:username>/', views.CustomerProfileDetailView.as_view(), name='customer_detail_admin'), # Ver perfil de un usuario específico
]