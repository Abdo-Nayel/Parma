# LyomasPharmacy — نظام محاسبة الصيدلية
# LyomasTech

## التشغيل السريع

```powershell
cd E:\LyomasPharmacy
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_pharmacy
python manage.py runserver
```

**الدخول:** `admin` / `admin123`

## هيكل النظام

| الوحدة | الوصف |
|--------|--------|
| **المخازن** | Warehouse |
| **الأصناف الرئيسية** | DrugCategory |
| **الشركات المنتجة** | DrugCompany |
| **الأصناف الفرعية** | Product (اسم + شركة + تكلفة + بيع) |
| **الموردين / العملاء** | Supplier / Customer |
| **المشتريات / المبيعات** | PurchaseInvoice / SalesInvoice |
| **المصروفات** | Expense |

قاعدة البيانات: `pharmacy.db` (SQLite)
