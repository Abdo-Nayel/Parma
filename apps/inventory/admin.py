from django.contrib import admin
from .models import Warehouse, DrugCategory, DrugCompany, Product, StockLot, StockMovement

admin.site.register(Warehouse)
admin.site.register(DrugCategory)
admin.site.register(DrugCompany)
admin.site.register(Product)
admin.site.register(StockLot)
admin.site.register(StockMovement)
