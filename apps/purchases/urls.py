from django.urls import path
from . import views

urlpatterns = [
    path('', views.purchase_list, name='purchase_list'),
    path('add/', views.purchase_add, name='purchase_add'),
    path('supplier-lookup/', views.supplier_lookup, name='supplier_lookup'),
    path('product-lookup/', views.product_lookup, name='purchase_product_lookup'),
    path('<int:pk>/edit/', views.purchase_form, name='purchase_edit'),
    path('<int:pk>/delete/', views.purchase_delete, name='purchase_delete'),
]
