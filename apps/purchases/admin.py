from django.contrib import admin
from .models import PurchaseInvoice, PurchaseLine

class PurchaseLineInline(admin.TabularInline):
    model = PurchaseLine
    extra = 1

admin.site.register(PurchaseInvoice, inlines=[PurchaseLineInline])
