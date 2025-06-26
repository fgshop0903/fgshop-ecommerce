from django.urls import path
from . import views

app_name = 'mydeliveries'

urlpatterns = [
    path('seguimiento/', views.public_order_tracking_view, name='public_order_tracking'),
    path('admin/listado/', views.DeliveryListView.as_view(), name='delivery_list'),
    path('admin/registrar/', views.DeliveryCreateView.as_view(), name='delivery_create'),
    path('admin/<int:pk>/actualizar/', views.DeliveryUpdateView.as_view(), name='delivery_update'),
    path('admin/<int:pk>/detalle/', views.DeliveryDetailView.as_view(), name='delivery_detail'),
]