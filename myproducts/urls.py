from django.urls import path
from . import views

app_name = 'myproducts'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('categorias/', views.CategoryListView.as_view(), name='category_list'),
    path('categoria/<path:category_path>/', views.ProductListView.as_view(), name='product_list_by_category'),
    path('marcas/<slug:brand_slug>/', views.ProductListByBrandView.as_view(), name='product_list_by_brand'),
    path('proveedores/<int:supplier_pk>/', views.ProductListBySupplierView.as_view(), name='product_list_by_supplier'),
    path('producto/nuevo/', views.ProductCreateView.as_view(), name='product_create'),
    path('producto/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('producto/<slug:slug>/editar/', views.ProductUpdateView.as_view(), name='product_update'),
    path('producto/<slug:slug>/eliminar/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('buscar/', views.ProductSearchView.as_view(), name='product_search'),
    path('ofertas/', views.sale_product_list_view, name='sale_list'),
]
