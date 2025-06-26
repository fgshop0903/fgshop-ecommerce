from django.urls import path
from . import views

app_name = 'myorders'

urlpatterns = [
    path('historial/', views.OrderHistoryView.as_view(), name='order_history'),
    path('<uuid:order_id>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('admin/listado/', views.OrderAdminListView.as_view(), name='order_list_admin'),
    path('admin/<uuid:order_id>/', views.OrderDetailView.as_view(), name='order_detail_admin'),
    path('api/variant-details/<int:variant_id>/', views.get_variant_details, name='get_variant_details'),
]