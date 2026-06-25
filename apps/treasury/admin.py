from django.contrib import admin
from .models import Bank, ExpenseCategory, Expense

admin.site.register(Bank)
admin.site.register(ExpenseCategory)
admin.site.register(Expense)
