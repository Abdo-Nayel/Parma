"""التحقق قبل الحذف — لا يُحذف السجل إذا كان مربوطاً بحركات أخرى."""
from decimal import Decimal

from django.apps import apps


def _blockers(*reasons):
    return [r for r in reasons if r]


def warehouse_blockers(obj):
    StockLot = apps.get_model('inventory', 'StockLot')
    StockMovement = apps.get_model('inventory', 'StockMovement')
    PurchaseInvoice = apps.get_model('purchases', 'PurchaseInvoice')
    SalesInvoice = apps.get_model('sales', 'SalesInvoice')
    return _blockers(
        'مرتبط بفواتير مشتريات' if PurchaseInvoice.objects.filter(warehouse=obj).exists() else '',
        'مرتبط بفواتير مبيعات' if SalesInvoice.objects.filter(warehouse=obj).exists() else '',
        'مرتبط بحركات مخزنية' if StockMovement.objects.filter(warehouse=obj).exists() else '',
        'يحتوي على أرصدة مخزنية' if StockLot.objects.filter(warehouse=obj, quantity__gt=0).exists() else '',
    )


def category_blockers(obj):
    return _blockers(
        'مرتبط بأصناف فرعية' if obj.products.exists() else '',
    )


def company_blockers(obj):
    return _blockers(
        'مرتبط بأصناف فرعية' if obj.products.exists() else '',
    )


def product_blockers(obj):
    StockLot = apps.get_model('inventory', 'StockLot')
    StockMovement = apps.get_model('inventory', 'StockMovement')
    PurchaseLine = apps.get_model('purchases', 'PurchaseLine')
    SalesLine = apps.get_model('sales', 'SalesLine')
    return _blockers(
        'له رصيد مخزني' if StockLot.objects.filter(product=obj, quantity__gt=0).exists() else '',
        'مرتبط بفواتير مشتريات' if PurchaseLine.objects.filter(product=obj).exists() else '',
        'مرتبط بفواتير مبيعات' if SalesLine.objects.filter(product=obj).exists() else '',
        'مرتبط بحركات مخزنية' if StockMovement.objects.filter(product=obj).exists() else '',
    )


def supplier_blockers(obj):
    PurchaseInvoice = apps.get_model('purchases', 'PurchaseInvoice')
    return _blockers(
        'مرتبط بفواتير مشتريات' if PurchaseInvoice.objects.filter(supplier=obj).exists() else '',
        'له رصيد مستحق' if obj.balance and obj.balance != Decimal('0') else '',
    )


def customer_blockers(obj):
    SalesInvoice = apps.get_model('sales', 'SalesInvoice')
    return _blockers(
        'مرتبط بفواتير مبيعات' if SalesInvoice.objects.filter(customer=obj).exists() else '',
        'له رصيد مستحق' if obj.balance and obj.balance != Decimal('0') else '',
    )


def purchase_invoice_blockers(obj):
    StockMovement = apps.get_model('inventory', 'StockMovement')
    if obj.status == obj.Status.POSTED:
        return ['فاتورة مرحّلة ومرتبطة بحركات مخزنية']
    return _blockers(
        'مرتبطة بحركات مخزنية' if StockMovement.objects.filter(reference=obj.invoice_number).exists() else '',
    )


def sales_invoice_blockers(obj):
    StockMovement = apps.get_model('inventory', 'StockMovement')
    if obj.status == obj.Status.POSTED:
        return ['فاتورة مرحّلة ومرتبطة بحركات مخزنية']
    return _blockers(
        'مرتبطة بحركات مخزنية' if StockMovement.objects.filter(reference=obj.invoice_number).exists() else '',
    )


def expense_blockers(obj):
    return []


def expense_category_blockers(obj):
    return _blockers(
        'مرتبط بمصروفات' if obj.expenses.exists() else '',
    )


def branch_blockers(obj):
    User = apps.get_model('users', 'User')
    Warehouse = apps.get_model('inventory', 'Warehouse')
    Bank = apps.get_model('treasury', 'Bank')
    return _blockers(
        'مرتبط بمستخدمين' if User.objects.filter(branch=obj).exists() else '',
        'مرتبط بمخازن' if Warehouse.objects.filter(branch=obj).exists() else '',
        'مرتبط ببنوك' if Bank.objects.filter(branch=obj).exists() else '',
    )


def bank_blockers(obj):
    Expense = apps.get_model('treasury', 'Expense')
    return _blockers(
        'مرتبط بمصروفات' if Expense.objects.filter(bank=obj).exists() else '',
    )


def user_blockers(obj):
    return _blockers(
        'لا يمكن حذف المستخدم الحالي' if obj.pk else '',
        'لا يمكن حذف آخر مدير نظام' if obj.is_superuser and obj.__class__.objects.filter(is_superuser=True).count() <= 1 else '',
    )
