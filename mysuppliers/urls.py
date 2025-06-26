from django.urls import path
from . import views

app_name = 'mysuppliers'

urlpatterns = [
    path('', views.SupplierListView.as_view(), name='supplier_list'),
    path('nuevo/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),
    path('<int:pk>/editar/', views.SupplierUpdateView.as_view(), name='supplier_update'),
    path('<int:pk>/eliminar/', views.SupplierDeleteView.as_view(), name='supplier_delete'),
]