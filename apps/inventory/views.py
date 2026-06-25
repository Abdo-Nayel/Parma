from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F, DecimalField
from datetime import date, timedelta
from decimal import Decimal

from apps.core.pagination import paginate_queryset
from apps.core.permissions import require_module
from apps.core.views import delete_confirm
from apps.core.delete_checks import (
    warehouse_blockers, category_blockers, company_blockers, product_blockers,
)
from apps.pharmacy.models import Branch, BarcodeLabelSettings
from .models import Warehouse, DrugCategory, DrugCompany, Product, StockLot, StockMovement
from .services import apply_stock_movement


from apps.core.codes import next_serial


def _next_code(model, prefix, field='code'):
    return next_serial(model, field)


# ─── المخازن ───
@login_required
@require_module('warehouses', 'view')
def warehouse_list(request):
    q = request.GET.get('q', '')
    items = Warehouse.objects.select_related('branch').all()
    if q:
        items = items.filter(Q(name__icontains=q) | Q(code__icontains=q))
    page_obj = paginate_queryset(request, items, per_page=25)
    return render(request, 'inventory/warehouse_list.html', {
        'page_title': 'المخازن', 'items': page_obj, 'page_obj': page_obj, 'q': q,
    })


@login_required
@require_module('warehouses', 'add')
def warehouse_form(request, pk=None):
    obj = get_object_or_404(Warehouse, pk=pk) if pk else None
    branches = Branch.objects.filter(is_active=True)
    if request.method == 'POST':
        code = request.POST.get('code') or _next_code(Warehouse, 'WH')
        data = {
            'code': code,
            'name': request.POST['name'],
            'branch_id': request.POST.get('branch') or None,
            'location': request.POST.get('location', ''),
            'notes': request.POST.get('notes', ''),
            'is_active': request.POST.get('is_active') == 'on',
        }
        if obj:
            for k, v in data.items():
                setattr(obj, k, v)
            obj.save()
            messages.success(request, 'تم تحديث المخزن')
        else:
            Warehouse.objects.create(**data)
            messages.success(request, 'تم إضافة المخزن')
        return redirect('warehouse_list')
    return render(request, 'inventory/warehouse_form.html', {
        'page_title': 'تعديل مخزن' if obj else 'إضافة مخزن',
        'obj': obj,
        'branches': branches,
        'suggested_code': obj.code if obj else _next_code(Warehouse, 'WH'),
    })


@login_required
def warehouse_delete(request, pk):
    return delete_confirm(
        request, Warehouse, pk, warehouse_blockers, 'warehouse_list', 'warehouses',
        object_label=lambda o: o.name, page_title='حذف مخزن',
    )


# ─── الأصناف الرئيسية ───
@login_required
def category_list(request):
    q = request.GET.get('q', '')
    items = DrugCategory.objects.all()
    if q:
        items = items.filter(Q(name__icontains=q) | Q(code__icontains=q))
    return render(request, 'inventory/category_list.html', {'page_title': 'الأصناف الرئيسية', 'items': items, 'q': q})


@login_required
def category_form(request, pk=None):
    obj = get_object_or_404(DrugCategory, pk=pk) if pk else None
    if request.method == 'POST':
        data = {
            'code': request.POST.get('code') or _next_code(DrugCategory, 'CAT'),
            'name': request.POST['name'],
            'description': request.POST.get('description', ''),
            'is_active': request.POST.get('is_active') == 'on',
        }
        if obj:
            for k, v in data.items():
                setattr(obj, k, v)
            obj.save()
            messages.success(request, 'تم التحديث')
        else:
            DrugCategory.objects.create(**data)
            messages.success(request, 'تم الإضافة')
        return redirect('category_list')
    return render(request, 'inventory/category_form.html', {
        'page_title': 'تعديل صنف رئيسي' if obj else 'إضافة صنف رئيسي',
        'obj': obj,
        'suggested_code': obj.code if obj else _next_code(DrugCategory, 'CAT'),
    })


# ─── الشركات المنتجة ───
@login_required
def company_list(request):
    q = request.GET.get('q', '')
    items = DrugCompany.objects.all()
    if q:
        items = items.filter(name__icontains=q)
    return render(request, 'inventory/company_list.html', {'page_title': 'الشركات المنتجة', 'items': items, 'q': q})


@login_required
def company_form(request, pk=None):
    obj = get_object_or_404(DrugCompany, pk=pk) if pk else None
    if request.method == 'POST':
        data = {
            'code': request.POST.get('code') or _next_code(DrugCompany, 'CO'),
            'name': request.POST['name'],
            'country': request.POST.get('country', ''),
            'phone': request.POST.get('phone', ''),
            'is_active': request.POST.get('is_active') == 'on',
        }
        if obj:
            for k, v in data.items():
                setattr(obj, k, v)
            obj.save()
            messages.success(request, 'تم التحديث')
        else:
            DrugCompany.objects.create(**data)
            messages.success(request, 'تم الإضافة')
        return redirect('company_list')
    return render(request, 'inventory/company_form.html', {
        'page_title': 'تعديل شركة' if obj else 'إضافة شركة منتجة',
        'obj': obj,
        'suggested_code': obj.code if obj else _next_code(DrugCompany, 'CO'),
    })


# ─── الأصناف الفرعية ───
@login_required
def product_list(request):
    q = request.GET.get('q', '')
    items = Product.objects.select_related('category', 'company').annotate(
        total_qty=Sum('stock_lots__quantity')
    )
    if q:
        items = items.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(barcode__icontains=q))
    page_obj = paginate_queryset(request, items, per_page=50)
    return render(request, 'inventory/product_list.html', {
        'page_title': 'الأصناف الفرعية',
        'items': page_obj,
        'page_obj': page_obj,
        'q': q,
    })


@login_required
def product_form(request, pk=None):
    obj = get_object_or_404(Product, pk=pk) if pk else None
    categories = DrugCategory.objects.filter(is_active=True)
    companies = DrugCompany.objects.filter(is_active=True)
    if request.method == 'POST':
        data = {
            'sku': request.POST.get('sku') or _next_code(Product, '', 'sku'),
            'name': request.POST['name'],
            'category_id': request.POST['category'],
            'company_id': request.POST['company'],
            'unit': request.POST.get('unit', 'box'),
            'barcode': request.POST.get('barcode', ''),
            'cost_price': request.POST.get('cost_price', 0) or 0,
            'sale_price': request.POST.get('sale_price', 0) or 0,
            'min_stock': request.POST.get('min_stock', 0) or 0,
            'max_stock': request.POST.get('max_stock', 0) or 0,
            'notes': request.POST.get('notes', ''),
            'is_active': request.POST.get('is_active') == 'on',
        }
        if obj:
            for k, v in data.items():
                setattr(obj, k, v)
            obj.save()
            messages.success(request, 'تم تحديث الصنف')
        else:
            Product.objects.create(**data, created_by=request.user)
            messages.success(request, 'تم إضافة الصنف')
        return redirect('product_list')
    return render(request, 'inventory/product_form.html', {
        'page_title': 'تعديل صنف' if obj else 'إضافة صنف فرعي',
        'obj': obj,
        'categories': categories,
        'companies': companies,
        'units': Product.Unit.choices,
        'suggested_sku': obj.sku if obj else _next_code(Product, '', 'sku'),
    })


# ─── رصيد افتتاحي ───
@login_required
def opening_stock(request):
    warehouses = Warehouse.objects.filter(is_active=True).only('id', 'name')
    products = Product.objects.filter(is_active=True).only('id', 'name').order_by('name')
    if request.method == 'POST':
        try:
            apply_stock_movement(
                'opening',
                products.get(pk=request.POST['product']),
                warehouses.get(pk=request.POST['warehouse']),
                request.POST['quantity'],
                request.POST.get('unit_cost', 0),
                notes=request.POST.get('notes', ''),
                user=request.user,
            )
            messages.success(request, 'تم تسجيل الرصيد الافتتاحي')
            return redirect('stock_report')
        except Exception as e:
            messages.error(request, str(e))
    return render(request, 'inventory/opening_stock.html', {
        'page_title': 'رصيد افتتاحي',
        'warehouses': warehouses,
        'products': products,
    })


@login_required
def stock_report(request):
    """استعلام مخزون — بحث/سكان + فلتر بالمجموعة والصنف والمخزن."""
    lots = StockLot.objects.select_related(
        'product', 'product__category', 'warehouse',
    ).filter(quantity__gt=0)

    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    product_id = request.GET.get('product')
    warehouse_id = request.GET.get('warehouse')

    if q:
        lots = lots.filter(
            Q(product__name__icontains=q)
            | Q(product__sku__icontains=q)
            | Q(product__barcode__icontains=q)
        )
    if category_id:
        lots = lots.filter(product__category_id=category_id)
    if product_id:
        lots = lots.filter(product_id=product_id)
    if warehouse_id:
        lots = lots.filter(warehouse_id=warehouse_id)

    rows = lots.values(
        'product_id',
        'product__sku',
        'product__name',
        'product__barcode',
        'product__sale_price',
        'product__cost_price',
        'product__category__code',
        'product__category__name',
        'warehouse_id',
        'warehouse__code',
        'warehouse__name',
    ).annotate(total_qty=Sum('quantity')).order_by('product__category__code', 'product__sku')

    page_obj = paginate_queryset(request, list(rows), per_page=50)
    products_qs = Product.objects.filter(is_active=True).select_related('category').order_by('name')
    if category_id:
        products_qs = products_qs.filter(category_id=category_id)

    return render(request, 'inventory/stock_report.html', {
        'page_title': 'استعلام مخزون',
        'rows': page_obj,
        'page_obj': page_obj,
        'warehouses': Warehouse.objects.filter(is_active=True).order_by('code'),
        'categories': DrugCategory.objects.filter(is_active=True).order_by('code'),
        'products': products_qs,
        'q': q,
        'selected_category': category_id,
        'selected_product': product_id,
        'selected_warehouse': warehouse_id,
    })


@login_required
def expiry_report(request):
    """تقرير صلاحيات قريبة من الانتهاء."""
    today = date.today()
    lots = StockLot.objects.select_related(
        'product', 'product__category', 'warehouse',
    ).filter(quantity__gt=0, expiry_date__isnull=False)

    expiry_from = request.GET.get('expiry_from')
    expiry_to = request.GET.get('expiry_to')
    warehouse_id = request.GET.get('warehouse')
    q = request.GET.get('q', '').strip()

    if not expiry_from:
        expiry_from = today.isoformat()
    if not expiry_to:
        expiry_to = (today + timedelta(days=90)).isoformat()

    lots = lots.filter(expiry_date__gte=expiry_from, expiry_date__lte=expiry_to)
    if warehouse_id:
        lots = lots.filter(warehouse_id=warehouse_id)
    if q:
        lots = lots.filter(
            Q(product__name__icontains=q)
            | Q(product__sku__icontains=q)
            | Q(product__barcode__icontains=q)
            | Q(batch_number__icontains=q)
        )

    lots = lots.order_by('expiry_date', 'product__name')
    page_obj = paginate_queryset(request, lots, per_page=50)

    return render(request, 'inventory/expiry_report.html', {
        'page_title': 'تقرير صلاحيات منتهية / قريبة',
        'lots': page_obj,
        'page_obj': page_obj,
        'warehouses': Warehouse.objects.filter(is_active=True).order_by('code'),
        'expiry_from': expiry_from,
        'expiry_to': expiry_to,
        'selected_warehouse': warehouse_id,
        'q': q,
        'today': today,
    })


@login_required
def stock_valuation(request):
    """تقييم المخزون — تكلفة وسعر بيع مع إجماليات."""
    group_by = request.GET.get('group_by', 'product')
    warehouse_id = request.GET.get('warehouse')
    category_id = request.GET.get('category')

    lots = StockLot.objects.filter(quantity__gt=0).select_related('product', 'product__category')
    if warehouse_id:
        lots = lots.filter(warehouse_id=warehouse_id)
    if category_id:
        lots = lots.filter(product__category_id=category_id)

    rows = []
    total_qty = Decimal('0')
    total_cost = Decimal('0')
    total_sale = Decimal('0')

    if group_by == 'category':
        grouped = lots.values(
            'product__category_id',
            'product__category__code',
            'product__category__name',
        ).annotate(
            total_qty=Sum('quantity'),
            total_cost=Sum(F('quantity') * F('product__cost_price'), output_field=DecimalField()),
            total_sale=Sum(F('quantity') * F('product__sale_price'), output_field=DecimalField()),
        ).order_by('product__category__code')
        for g in grouped:
            qty = g['total_qty'] or Decimal('0')
            cost = g['total_cost'] or Decimal('0')
            sale = g['total_sale'] or Decimal('0')
            rows.append({
                'code': g['product__category__code'],
                'name': g['product__category__name'],
                'qty': qty,
                'cost_value': cost,
                'sale_value': sale,
            })
            total_qty += qty
            total_cost += cost
            total_sale += sale
    else:
        grouped = lots.values(
            'product_id',
            'product__sku',
            'product__name',
            'product__category__code',
            'product__category__name',
            'product__cost_price',
            'product__sale_price',
        ).annotate(total_qty=Sum('quantity')).order_by('product__category__code', 'product__sku')
        for g in grouped:
            qty = g['total_qty'] or Decimal('0')
            cost = qty * (g['product__cost_price'] or Decimal('0'))
            sale = qty * (g['product__sale_price'] or Decimal('0'))
            rows.append({
                'code': g['product__sku'],
                'name': g['product__name'],
                'category': f"{g['product__category__code']} — {g['product__category__name']}",
                'qty': qty,
                'unit_cost': g['product__cost_price'],
                'unit_sale': g['product__sale_price'],
                'cost_value': cost,
                'sale_value': sale,
            })
            total_qty += qty
            total_cost += cost
            total_sale += sale

    page_obj = paginate_queryset(request, rows, per_page=50)
    return render(request, 'inventory/stock_valuation.html', {
        'page_title': 'تقييم المخزون',
        'rows': page_obj,
        'page_obj': page_obj,
        'group_by': group_by,
        'warehouses': Warehouse.objects.filter(is_active=True).order_by('code'),
        'categories': DrugCategory.objects.filter(is_active=True).order_by('code'),
        'selected_warehouse': warehouse_id,
        'selected_category': category_id,
        'total_qty': total_qty,
        'total_cost': total_cost,
        'total_sale': total_sale,
    })


@login_required
def category_delete(request, pk):
    return delete_confirm(
        request, DrugCategory, pk, category_blockers, 'category_list', 'categories',
        object_label=lambda o: o.name, page_title='حذف صنف رئيسي',
    )


@login_required
def company_delete(request, pk):
    return delete_confirm(
        request, DrugCompany, pk, company_blockers, 'company_list', 'companies',
        object_label=lambda o: o.name, page_title='حذف شركة',
    )


@login_required
def product_delete(request, pk):
    return delete_confirm(
        request, Product, pk, product_blockers, 'product_list', 'products',
        object_label=lambda o: o.name, page_title='حذف صنف',
    )


@login_required
@require_module('products', 'view')
def product_label_print(request, pk):
    product = get_object_or_404(Product.objects.select_related('company'), pk=pk)
    label_settings = BarcodeLabelSettings.get_solo()
    copies = int(request.GET.get('copies', label_settings.copies_default))
    copies = max(1, min(copies, 100))
    barcode_value = product.barcode or product.sku
    return render(request, 'inventory/product_label_print.html', {
        'product': product,
        'settings': label_settings,
        'copies': copies,
        'copy_range': range(copies),
        'barcode_value': barcode_value,
    })
