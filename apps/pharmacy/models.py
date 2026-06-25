from django.db import models


class PharmacyProfile(models.Model):
    """بيانات الصيدلية الأساسية"""
    name = models.CharField('اسم الصيدلية', max_length=200)
    owner_name = models.CharField('اسم المالك', max_length=120, blank=True)
    phone = models.CharField('الهاتف', max_length=30, blank=True)
    address = models.CharField('العنوان', max_length=255, blank=True)
    tax_number = models.CharField('الرقم الضريبي', max_length=50, blank=True)
    logo = models.ImageField('الشعار', upload_to='logos/', blank=True, null=True)
    currency = models.CharField('العملة', max_length=10, default='ج.م')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'بيانات الصيدلية'
        verbose_name_plural = 'بيانات الصيدلية'

    def __str__(self):
        return self.name


class Branch(models.Model):
    """فرع الصيدلية"""
    code = models.CharField('كود الفرع', max_length=20, unique=True)
    name = models.CharField('اسم الفرع', max_length=120)
    address = models.CharField('العنوان', max_length=255, blank=True)
    phone = models.CharField('الهاتف', max_length=30, blank=True)
    is_active = models.BooleanField('نشط', default=True)

    class Meta:
        verbose_name = 'فرع'
        verbose_name_plural = 'الفروع'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} — {self.name}'


class BarcodeLabelSettings(models.Model):
    """إعدادات طباعة ليبل الباركود"""
    label_width_mm = models.PositiveIntegerField('عرض الليبل (مم)', default=50)
    label_height_mm = models.PositiveIntegerField('ارتفاع الليبل (مم)', default=30)
    show_product_name = models.BooleanField('إظهار اسم الدواء', default=True)
    show_sku = models.BooleanField('إظهار كود الصنف', default=True)
    show_price = models.BooleanField('إظهار السعر', default=True)
    show_company = models.BooleanField('إظهار الشركة', default=False)
    font_size = models.PositiveIntegerField('حجم الخط', default=10)
    barcode_height = models.PositiveIntegerField('ارتفاع الباركود', default=40)
    copies_default = models.PositiveIntegerField('عدد النسخ الافتراضي', default=1)

    class Meta:
        verbose_name = 'إعدادات ليبل الباركود'
        verbose_name_plural = 'إعدادات ليبل الباركود'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'إعدادات ليبل الباركود'


class ReceiptSettings(models.Model):
    """إعدادات طباعة إيصال البيع — Xprinter 80mm"""
    header_text = models.TextField('نص الهيدر', blank=True, default='شكراً لزيارتكم')
    footer_text = models.TextField('نص الفوتر', blank=True, default='بالشفاء العاجل')
    receipt_logo = models.ImageField('لوجو الإيصال', upload_to='receipts/', blank=True, null=True)
    use_pharmacy_logo = models.BooleanField('استخدام شعار الصيدلية', default=True)
    show_logo = models.BooleanField('إظهار اللوجو', default=True)
    paper_width_mm = models.PositiveIntegerField('عرض الورق (مم)', default=80)
    title_font_size = models.PositiveIntegerField('حجم خط العنوان', default=15)
    body_font_size = models.PositiveIntegerField('حجم خط المحتوى', default=12)
    show_cashier = models.BooleanField('إظهار الكاشير', default=True)
    show_customer = models.BooleanField('إظهار بيانات العميل', default=True)
    show_discount = models.BooleanField('إظهار الخصم', default=True)
    auto_print = models.BooleanField('طباعة تلقائية بعد الترحيل', default=False)

    class Meta:
        verbose_name = 'إعدادات إيصال البيع'
        verbose_name_plural = 'إعدادات إيصال البيع'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'إعدادات إيصال البيع'
