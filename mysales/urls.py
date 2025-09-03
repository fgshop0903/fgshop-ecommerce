from django.urls import path
from . import views

app_name = 'mysales'

urlpatterns = [
    path('historial/', views.OrderHistoryView.as_view(), name='order_history'),
    path('<uuid:order_id>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('admin/listado/', views.OrderAdminListView.as_view(), name='order_list_admin'),
    path('admin/<uuid:order_id>/', views.OrderDetailView.as_view(), name='order_detail_admin'),
    path('<uuid:order_id>/pdf/', views.generate_invoice_pdf, name='order_invoice_pdf'),
    path('<uuid:order_id>/orden-pedido/pdf/', views.generar_orden_pedido_pdf, name='order_pedido_pdf'),
    path('<uuid:order_id>/nota-venta/pdf/', views.generar_nota_venta_pdf, name='order_nota_venta_pdf'),
    path('api/variant-details/<int:variant_id>/', views.get_variant_details, name='get_variant_details'),
    path('venta-cuotas/<int:sale_id>/acuerdo/pdf/', views.generar_acuerdo_cuotas_pdf, name='installment_sale_agreement_pdf'),
    path('pago-cuota/<int:payment_id>/recibo/pdf/', views.generar_recibo_cuota_pdf, name='installment_payment_receipt_pdf'),

]