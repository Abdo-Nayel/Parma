from django.urls import path
from . import views

urlpatterns = [
    path('', views.return_list, name='return_list'),
    path('add/', views.return_add, name='return_add'),
    path('lookup/product/', views.product_lookup, name='return_product_lookup'),
    path('<int:pk>/edit/', views.return_edit, name='return_edit'),
    path('<int:pk>/', views.return_detail, name='return_detail'),
]
