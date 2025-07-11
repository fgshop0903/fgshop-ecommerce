from django.urls import path
from . import views

app_name = 'mycart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('remove/<int:variant_id>/', views.cart_remove, name='cart_remove'),
    path('update/<int:variant_id>/', views.cart_update, name='cart_update'),
    path('clear/', views.cart_clear, name='cart_clear'),
    path('toggle-selection/<int:variant_id>/', views.cart_toggle_selection, name='cart_toggle_selection'),
    path('bulk-toggle-selection/', views.cart_bulk_toggle_selection, name='cart_bulk_toggle_selection'),
]