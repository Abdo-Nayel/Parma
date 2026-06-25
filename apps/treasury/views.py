from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from decimal import Decimal

from apps.core.pagination import paginate_queryset
from apps.core.views import delete_confirm
from apps.core.delete_checks import expense_blockers
from apps.purchases.models import PurchaseInvoice, PurchasePayment
from apps.sales.models import SalesInvoice, SalesPayment
from apps.parties.models import SupplierPayment, CustomerPayment
from apps.returns.models import ReturnDocument, ReturnPayment
from apps.core.ledger_export import export_ledger_excel, export_ledger_pdf
from .models import ExpenseCategory, Expense, Bank, CashBox


def _parse_dates(request):
    return request.GET.get('date_from', ''), request.GET.get('date_to', '')


def _filter_by_date(qs, date_field, date_from, date_to):
    if date_from:
        qs = qs.filter(**{f'{date_field}__gte': date_from})
    if date_to:
        qs = qs.filter(**{f'{date_field}__lte': date_to})
    return qs


def _build_ledger_entries(
    pay_out_qs, exp_qs, sup_pay_qs, pay_in_qs=None, cust_pay_qs=None,
    ret_out_qs=None, ret_in_qs=None,
):
    entries = []
    pay_in_qs = pay_in_qs or []
    cust_pay_qs = cust_pay_qs or []
    ret_out_qs = ret_out_qs or []
    ret_in_qs = ret_in_qs or []

    for pay in pay_out_qs:
        entries.append({
            'date': pay.invoice.date,
            'ref': pay.invoice.invoice_number,
            'desc': f'سداد مشتريات — {pay.invoice.supplier.name}',
            'out': pay.amount,
            'in': Decimal('0'),
        })
    for sp in sup_pay_qs:
        entries.append({
            'date': sp.date,
            'ref': sp.reference,
            'desc': f'سداد مورد — {sp.supplier.name}',
            'out': sp.amount,
            'in': Decimal('0'),
        })
    for exp in exp_qs:
        entries.append({
            'date': exp.date,
            'ref': getattr(exp.category, 'code', exp.category.name),
            'desc': exp.description or exp.category.name,
            'out': exp.amount,
            'in': Decimal('0'),
        })
    for pay in pay_in_qs:
        entries.append({
            'date': pay.invoice.date,
            'ref': pay.invoice.invoice_number,
            'desc': f'تحصيل مبيعات — {pay.invoice.buyer_display}',
            'out': Decimal('0'),
            'in': pay.amount,
        })
    for cp in cust_pay_qs:
        entries.append({
            'date': cp.date,
            'ref': cp.reference,
            'desc': f'تحصيل عميل — {cp.customer.name}',
            'out': Decimal('0'),
            'in': cp.amount,
        })
    for rp in ret_out_qs:
        entries.append({
            'date': rp.document.date,
            'ref': rp.document.return_number,
            'desc': f'استرداد مرتجع — {rp.document.party_display}',
            'out': rp.amount,
            'in': Decimal('0'),
        })
    for rp in ret_in_qs:
        entries.append({
            'date': rp.document.date,
            'ref': rp.document.return_number,
            'desc': f'تحصيل مرتجع — {rp.document.party_display}',
            'out': Decimal('0'),
            'in': rp.amount,
        })
    entries.sort(key=lambda e: e['date'], reverse=True)
    total_in = sum(e['in'] for e in entries)
    total_out = sum(e['out'] for e in entries)
    return entries, total_in, total_out


@login_required
def expense_list(request):
    q = request.GET.get('q', '')
    items = Expense.objects.select_related('category', 'bank').order_by('-date')
    if q:
        items = items.filter(Q(description__icontains=q) | Q(category__name__icontains=q))
    page_obj = paginate_queryset(request, items, per_page=25)
    return render(request, 'treasury/expense_list.html', {
        'page_title': 'المصروفات',
        'items': page_obj,
        'page_obj': page_obj,
        'q': q,
    })


@login_required
def expense_form(request, pk=None):
    obj = get_object_or_404(Expense, pk=pk) if pk else None
    categories = ExpenseCategory.objects.filter(is_active=True)
    banks = Bank.objects.filter(is_active=True)
    if request.method == 'POST':
        data = {
            'category_id': request.POST['category'],
            'bank_id': request.POST.get('bank') or None,
            'amount': request.POST['amount'],
            'date': request.POST['date'],
            'description': request.POST.get('description', ''),
        }
        if obj:
            for k, v in data.items():
                setattr(obj, k, v)
            obj.save()
            messages.success(request, 'تم تحديث المصروف')
        else:
            with transaction.atomic():
                expense = Expense.objects.create(**data, created_by=request.user)
                if expense.bank_id:
                    expense.bank.balance -= expense.amount
                    expense.bank.save(update_fields=['balance'])
                else:
                    cash = CashBox.get_main()
                    cash.balance -= expense.amount
                    cash.save(update_fields=['balance'])
            messages.success(request, 'تم تسجيل المصروف')
        return redirect('expense_list')
    return render(request, 'treasury/expense_form.html', {
        'page_title': 'تعديل مصروف' if obj else 'تسجيل مصروف',
        'obj': obj,
        'categories': categories,
        'banks': banks,
    })


@login_required
def expense_delete(request, pk):
    return delete_confirm(
        request, Expense, pk, expense_blockers, 'expense_list', 'expenses',
        object_label=lambda o: str(o), page_title='حذف مصروف',
    )


@login_required
def cash_ledger(request):
    date_from, date_to = _parse_dates(request)
    cash = CashBox.get_main()

    pay_out_qs = PurchasePayment.objects.filter(
        invoice__status='posted', payment_type='cash',
    ).select_related('invoice__supplier')
    pay_out_qs = _filter_by_date(pay_out_qs, 'invoice__date', date_from, date_to)

    pay_in_qs = SalesPayment.objects.filter(
        invoice__status='posted', payment_type='cash',
    ).select_related('invoice', 'invoice__customer')
    pay_in_qs = _filter_by_date(pay_in_qs, 'invoice__date', date_from, date_to)

    sup_pay_qs = SupplierPayment.objects.filter(payment_type='cash').select_related('supplier')
    sup_pay_qs = _filter_by_date(sup_pay_qs, 'date', date_from, date_to)

    cust_pay_qs = CustomerPayment.objects.filter(payment_type='cash').select_related('customer')
    cust_pay_qs = _filter_by_date(cust_pay_qs, 'date', date_from, date_to)

    exp_qs = Expense.objects.filter(bank__isnull=True).select_related('category')
    exp_qs = _filter_by_date(exp_qs, 'date', date_from, date_to)

    ret_out_qs = ReturnPayment.objects.filter(
        document__status='posted',
        document__kind=ReturnDocument.Kind.SALES,
        payment_type='cash',
    ).select_related('document')
    ret_out_qs = _filter_by_date(ret_out_qs, 'document__date', date_from, date_to)

    ret_in_qs = ReturnPayment.objects.filter(
        document__status='posted',
        document__kind=ReturnDocument.Kind.PURCHASE,
        payment_type='cash',
    ).select_related('document')
    ret_in_qs = _filter_by_date(ret_in_qs, 'document__date', date_from, date_to)

    entries, total_in, total_out = _build_ledger_entries(
        pay_out_qs, exp_qs, sup_pay_qs, pay_in_qs, cust_pay_qs, ret_out_qs, ret_in_qs,
    )
    net_balance = total_in - total_out

    export_fmt = request.GET.get('export')
    title = f'كشف الخزنة النقدية — {cash.name}'
    if export_fmt == 'excel':
        return export_ledger_excel(
            entries, total_in, total_out, net_balance, cash.balance,
            title, 'cash-ledger.xlsx',
        )
    if export_fmt == 'pdf':
        return export_ledger_pdf(
            entries, total_in, total_out, net_balance, cash.balance,
            title, 'cash-ledger.pdf',
        )

    return render(request, 'treasury/cash_ledger.html', {
        'page_title': f'كشف الخزنة النقدية — {cash.name}',
        'cash': cash,
        'current_balance': cash.balance,
        'entries': entries,
        'date_from': date_from,
        'date_to': date_to,
        'total_in': total_in,
        'total_out': total_out,
        'net_balance': net_balance,
    })


@login_required
def bank_ledger(request):
    date_from, date_to = _parse_dates(request)
    bank_id = request.GET.get('bank')
    bank_q = request.GET.get('q', '').strip()
    banks = Bank.objects.filter(is_active=True).order_by('code')

    if bank_q and not bank_id:
        match = banks.filter(Q(name__icontains=bank_q) | Q(code__icontains=bank_q)).first()
        if match:
            bank_id = str(match.pk)

    bank = get_object_or_404(Bank, pk=bank_id) if bank_id else banks.first()

    entries = []
    total_in = Decimal('0')
    total_out = Decimal('0')
    if bank:
        pay_out_qs = PurchasePayment.objects.filter(
            invoice__status='posted', payment_type='bank', bank=bank,
        ).select_related('invoice__supplier')
        pay_out_qs = _filter_by_date(pay_out_qs, 'invoice__date', date_from, date_to)

        pay_in_qs = SalesPayment.objects.filter(
            invoice__status='posted', payment_type='bank', bank=bank,
        ).select_related('invoice', 'invoice__customer')
        pay_in_qs = _filter_by_date(pay_in_qs, 'invoice__date', date_from, date_to)

        sup_pay_qs = SupplierPayment.objects.filter(payment_type='bank', bank=bank).select_related('supplier')
        sup_pay_qs = _filter_by_date(sup_pay_qs, 'date', date_from, date_to)

        cust_pay_qs = CustomerPayment.objects.filter(payment_type='bank', bank=bank).select_related('customer')
        cust_pay_qs = _filter_by_date(cust_pay_qs, 'date', date_from, date_to)

        exp_qs = Expense.objects.filter(bank=bank).select_related('category')
        exp_qs = _filter_by_date(exp_qs, 'date', date_from, date_to)

        ret_out_qs = ReturnPayment.objects.filter(
            document__status='posted',
            document__kind=ReturnDocument.Kind.SALES,
            payment_type='bank', bank=bank,
        ).select_related('document')
        ret_out_qs = _filter_by_date(ret_out_qs, 'document__date', date_from, date_to)

        ret_in_qs = ReturnPayment.objects.filter(
            document__status='posted',
            document__kind=ReturnDocument.Kind.PURCHASE,
            payment_type='bank', bank=bank,
        ).select_related('document')
        ret_in_qs = _filter_by_date(ret_in_qs, 'document__date', date_from, date_to)

        entries, total_in, total_out = _build_ledger_entries(
            pay_out_qs, exp_qs, sup_pay_qs, pay_in_qs, cust_pay_qs, ret_out_qs, ret_in_qs,
        )

    net_balance = total_in - total_out

    export_fmt = request.GET.get('export')
    if bank and export_fmt == 'excel':
        return export_ledger_excel(
            entries, total_in, total_out, net_balance, bank.balance,
            f'كشف بنك — {bank.name}', 'bank-ledger.xlsx',
        )
    if bank and export_fmt == 'pdf':
        return export_ledger_pdf(
            entries, total_in, total_out, net_balance, bank.balance,
            f'كشف بنك — {bank.name}', 'bank-ledger.pdf',
        )

    return render(request, 'treasury/bank_ledger.html', {
        'page_title': f'كشف بنك — {bank.name}' if bank else 'كشف البنوك',
        'bank': bank,
        'banks': banks,
        'current_balance': bank.balance if bank else Decimal('0'),
        'entries': entries,
        'date_from': date_from,
        'date_to': date_to,
        'bank_q': bank_q,
        'selected_bank': bank_id or (str(bank.pk) if bank else ''),
        'total_in': total_in,
        'total_out': total_out,
        'net_balance': net_balance,
    })


@login_required
def treasury_ledger(request):
    """إعادة توجيه للخزنة النقدية."""
    return redirect('cash_ledger')
