from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.conf import settings


class Warehouse(models.Model):
    """المخزن"""
    code = models.CharField('الكود', max_length=20, unique=True)
    name = models.CharField('اسم المخزن', max_length=120)
    branch = models.ForeignKey(
        'pharmacy.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='الفرع',
        related_name='warehouses',
    )
    location = models.CharField('الموقع', max_length=200, blank=True)
    is_active = models.BooleanField('نشط', default=True)
    notes = models.TextField('ملاحظات', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'مخزن'
        verbose_name_plural = 'المخازن'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'


class DrugCategory(models.Model):
    """الصنف الرئيسي — مجموعة الأدوية"""
    code = models.CharField('الكود', max_length=20, unique=True)
    name = models.CharField('اسم المجموعة', max_length=150)
    description = models.TextField('الوصف', blank=True)
    is_active = models.BooleanField('نشط', default=True)

    class Meta:
        verbose_name = 'صنف رئيسي'
        verbose_name_plural = 'الأصناف الرئيسية'
        ordering = ['code']

    def __str__(self):
        return self.name


class DrugCompany(models.Model):
    """الشركة المنتجة"""
    code = models.CharField('الكود', max_length=20, unique=True)
    name = models.CharField('اسم الشركة', max_length=150)
    country = models.CharField('الدولة', max_length=80, blank=True)
    phone = models.CharField('الهاتف', max_length=30, blank=True)
    is_active = models.BooleanField('نشط', default=True)

    class Meta:
        verbose_name = 'شركة منتجة'
        verbose_name_plural = 'الشركات المنتجة'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """الصنف الفرعي — الدواء / المنتج"""
    class Unit(models.TextChoices):
        BOX = 'box', 'علبة'
        STRIP = 'strip', 'شريط'
        PIECE = 'piece', 'قطعة'
        BOTTLE = 'bottle', 'زجاجة'
        TUBE = 'tube', 'أنبوبة'

    sku = models.CharField('كود الصنف', max_length=30, unique=True)
    name = models.CharField('اسم الدواء', max_length=200)
    category = models.ForeignKey(DrugCategory, on_delete=models.PROTECT, verbose_name='الصنف الرئيسي', related_name='products')
    company = models.ForeignKey(DrugCompany, on_delete=models.PROTECT, verbose_name='الشركة المنتجة', related_name='products')
    unit = models.CharField('الوحدة', max_length=10, choices=Unit.choices, default=Unit.BOX)
    barcode = models.CharField('الباركود', max_length=50, blank=True)
    cost_price = models.DecimalField('تكلفة الشراء', max_digits=12, decimal_places=2, default=0)
    sale_price = models.DecimalField('سعر البيع', max_digits=12, decimal_places=2, default=0)
    min_stock = models.DecimalField('حد الطلب', max_digits=12, decimal_places=2, default=0)
    max_stock = models.DecimalField('الحد الأقصى', max_digits=12, decimal_places=2, default=0)
    expiry_alert_days = models.PositiveIntegerField('تنبيه قبل الانتهاء (يوم)', default=90)
    is_active = models.BooleanField('نشط', default=True)
    notes = models.TextField('ملاحظات', blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='products_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'صنف فرعي'
        verbose_name_plural = 'الأصناف الفرعية'
        ordering = ['name']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new or not self.barcode:
            from apps.core.codes import generate_product_barcode
            new_barcode = generate_product_barcode(self)
            if self.barcode != new_barcode:
                self.barcode = new_barcode
                super().save(update_fields=['barcode'])

    def __str__(self):
        return f'{self.sku} - {self.name}'

    @property
    def total_quantity(self):
        return self.stock_lots.aggregate(t=Sum('quantity'))['t'] or Decimal('0')

    @property
    def stock_value(self):
        return self.total_quantity * self.cost_price

    @property
    def is_low_stock(self):
        return self.total_quantity <= self.min_stock


class StockLot(models.Model):
    """رصيد الصنف في مخزن معين"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_lots', verbose_name='الصنف')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_lots', verbose_name='المخزن')
    quantity = models.DecimalField('الكمية', max_digits=12, decimal_places=2, default=0)
    batch_number = models.CharField('رقم التشغيلة', max_length=50, blank=True)
    expiry_date = models.DateField('تاريخ الصلاحية', null=True, blank=True)

    class Meta:
        verbose_name = 'رصيد مخزن'
        verbose_name_plural = 'أرصدة المخازن'
        unique_together = [['product', 'warehouse', 'batch_number']]

    def __str__(self):
        return f'{self.product.name} @ {self.warehouse.name}: {self.quantity}'

    @property
    def days_to_expiry(self):
        if not self.expiry_date:
            return None
        from datetime import date
        return (self.expiry_date - date.today()).days


class StockMovement(models.Model):
    """حركة مخزنية — تسوية / تحويل / رصيد افتتاحي"""
    class MoveType(models.TextChoices):
        OPENING = 'opening', 'رصيد افتتاحي'
        PURCHASE = 'purchase', 'مشتريات'
        SALE = 'sale', 'مبيعات'
        TRANSFER = 'transfer', 'تحويل'
        ADJUST_IN = 'adjust_in', 'تسوية إضافة'
        ADJUST_OUT = 'adjust_out', 'تسوية خصم'
        RETURN_IN = 'return_in', 'مرتجع شراء'
        RETURN_OUT = 'return_out', 'مرتجع بيع'

    move_type = models.CharField('نوع الحركة', max_length=15, choices=MoveType.choices)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='الصنف')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, verbose_name='المخزن')
    quantity = models.DecimalField('الكمية', max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField('تكلفة الوحدة', max_digits=12, decimal_places=2, default=0)
    reference = models.CharField('مرجع', max_length=50, blank=True)
    notes = models.TextField('ملاحظات', blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'حركة مخزنية'
        verbose_name_plural = 'الحركات المخزنية'
        ordering = ['-created_at']
