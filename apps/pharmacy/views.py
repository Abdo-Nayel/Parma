from datetime import date
from decimal import Decimal

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F

from apps.inventory.models import Product
from apps.sales.models import SalesInvoice
from apps.parties.models import Customer, Supplier


@login_required
def dashboard(request):
    today = date.today()
    products_count = Product.objects.filter(is_active=True).count()
    low_stock = Product.objects.filter(is_active=True).annotate(
        total_qty=Sum('stock_lots__quantity')
    ).filter(total_qty__lt=F('min_stock')).count()

    today_sales = SalesInvoice.objects.filter(
        status='posted', date=today
    ).aggregate(total=Sum('grand_total'))['total'] or Decimal('0')

    customers_count = Customer.objects.filter(is_active=True).count()
    suppliers_count = Supplier.objects.filter(is_active=True).count()

    recent_sales = SalesInvoice.objects.filter(
        status='posted'
    ).select_related('customer').order_by('-date', '-id')[:5]

    context = {
        'page_title': 'لوحة التحكم',
        'products_count': products_count,
        'low_stock': low_stock,
        'today_sales': today_sales,
        'customers_count': customers_count,
        'suppliers_count': suppliers_count,
        'recent_sales': recent_sales,
    }
    return render(request, 'dashboard/home.html', context)
