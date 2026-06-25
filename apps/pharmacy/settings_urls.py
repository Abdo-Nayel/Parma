from django.urls import path
from . import settings_views

urlpatterns = [
    path('', settings_views.settings_home, name='settings_home'),
    path('pharmacy/', settings_views.pharmacy_profile_form, name='pharmacy_profile'),
    path('branches/', settings_views.branch_list, name='branch_list'),
    path('branches/add/', settings_views.branch_form, name='branch_add'),
    path('branches/<int:pk>/edit/', settings_views.branch_form, name='branch_edit'),
    path('branches/<int:pk>/delete/', settings_views.branch_delete, name='branch_delete'),
    path('banks/', settings_views.bank_list, name='bank_list'),
    path('banks/add/', settings_views.bank_form, name='bank_add'),
    path('banks/<int:pk>/edit/', settings_views.bank_form, name='bank_edit'),
    path('banks/<int:pk>/delete/', settings_views.bank_delete, name='bank_delete'),
    path('users/', settings_views.user_list, name='user_list'),
    path('users/add/', settings_views.user_form, name='user_add'),
    path('users/<int:pk>/edit/', settings_views.user_form, name='user_edit'),
    path('users/<int:pk>/delete/', settings_views.user_delete, name='user_delete'),
    path('barcode/', settings_views.barcode_settings, name='barcode_settings'),
    path('receipt/', settings_views.receipt_settings, name='receipt_settings'),
]
