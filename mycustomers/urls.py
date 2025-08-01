from django.urls import path, include
from . import views

app_name = 'mycustomers'

urlpatterns = [
    
    # Gestión de Perfil de Usuario
    path('perfil/', views.CustomerProfileDetailView.as_view(), name='profile_detail_self'), # Ver perfil propio
    path('perfil/editar/', views.CustomerProfileUpdateView.as_view(), name='profile_update'),
    path('admin/listado/', views.CustomerListView.as_view(), name='customer_list_admin'),
    path('admin/perfil/<str:username>/', views.CustomerProfileDetailView.as_view(), name='customer_detail_admin'), # Ver perfil de un usuario específico
    path('direcciones/', views.AddressListView.as_view(), name='address_list'),
]