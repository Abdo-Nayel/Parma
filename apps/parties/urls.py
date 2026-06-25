from django.urls import path
from . import views

urlpatterns = [
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_form, name='supplier_add'),
    path('suppliers/<int:pk>/edit/', views.supplier_form, name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
    path('suppliers/balances/', views.supplier_balances, name='supplier_balances'),
    path('suppliers/statement/', views.supplier_statement, name='supplier_statement'),
    path('suppliers/payment/', views.supplier_payment, name='supplier_payment'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_form, name='customer_add'),
    path('customers/<int:pk>/edit/', views.customer_form, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    path('customers/balances/', views.customer_balances, name='customer_balances'),
    path('customers/statement/', views.customer_statement, name='customer_statement'),
    path('customers/payment/', views.customer_payment, name='customer_payment'),
]
