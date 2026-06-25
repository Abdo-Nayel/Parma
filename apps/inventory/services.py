from decimal import Decimal
from django.db import transaction
from .models import StockLot, StockMovement


@transaction.atomic
def apply_stock_movement(
    move_type, product, warehouse, quantity, unit_cost=0, reference='',
    notes='', user=None, batch_number='', expiry_date=None,
):
  """تطبيق حركة مخزنية وتحديث الرصيد"""
  qty = Decimal(str(quantity))
  if qty <= 0:
      raise ValueError('الكمية يجب أن تكون أكبر من صفر')

  is_out = move_type in ('sale', 'adjust_out', 'return_out', 'transfer')
  batch = batch_number or ''

  lot, _ = StockLot.objects.get_or_create(
      product=product,
      warehouse=warehouse,
      batch_number=batch,
      defaults={'quantity': 0, 'expiry_date': expiry_date},
  )
  if expiry_date and not lot.expiry_date:
      lot.expiry_date = expiry_date
      lot.save(update_fields=['expiry_date'])

  if is_out and lot.quantity < qty:
      raise ValueError(f'رصيد غير كافٍ. المتاح: {lot.quantity}')

  if is_out:
      lot.quantity -= qty
  else:
      lot.quantity += qty
  lot.save()

  StockMovement.objects.create(
      move_type=move_type,
      product=product,
      warehouse=warehouse,
      quantity=qty,
      unit_cost=unit_cost or product.cost_price,
      reference=reference,
      notes=notes,
      created_by=user,
  )
  return lot


@transaction.atomic
def deduct_stock_for_sale(product, warehouse, quantity, unit_cost=0, reference='', user=None):
    """خصم كمية البيع من أرصدة المخزن (الأقرب انتهاءً أولاً)."""
    remaining = Decimal(str(quantity))
    if remaining <= 0:
        raise ValueError('الكمية يجب أن تكون أكبر من صفر')

    lots = list(
        StockLot.objects.filter(
            product=product, warehouse=warehouse, quantity__gt=0,
        ).order_by('expiry_date', 'id')
    )
    available = sum(lot.quantity for lot in lots)
    if available < remaining:
        raise ValueError(f'رصيد غير كافٍ في المخزن. المتاح: {available}')

    cost = unit_cost or product.cost_price
    for lot in lots:
        if remaining <= 0:
            break
        take = min(lot.quantity, remaining)
        lot.quantity -= take
        lot.save(update_fields=['quantity'])
        StockMovement.objects.create(
            move_type='sale',
            product=product,
            warehouse=warehouse,
            quantity=take,
            unit_cost=cost,
            reference=reference,
            notes=f'تشغيلة: {lot.batch_number}' if lot.batch_number else '',
            created_by=user,
        )
        remaining -= take


@transaction.atomic
def restore_stock_from_sale(reference, user=None):
    """إرجاع مخزون فاتورة بيع ملغاة."""
    movements = list(StockMovement.objects.filter(reference=reference, move_type='sale'))
    for mv in movements:
        batch = ''
        if mv.notes.startswith('تشغيلة: '):
            batch = mv.notes.replace('تشغيلة: ', '', 1)
        apply_stock_movement(
            'return_in', mv.product, mv.warehouse, mv.quantity,
            mv.unit_cost, reference, notes='إلغاء بيع', user=user,
            batch_number=batch,
        )
    StockMovement.objects.filter(reference=reference, move_type='sale').delete()
