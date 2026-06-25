from django.contrib import admin
from .models import SalesInvoice, SalesLine

class SalesLineInline(admin.TabularInline):
    model = SalesLine
    extra = 1

admin.site.register(SalesInvoice, inlines=[SalesLineInline])
