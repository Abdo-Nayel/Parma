# LyomasPharmacy (Parma)

نظام محاسبة ومخزون صيدلية — Django 4.2

## تشغيل محلي (تطوير)

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r Requirements.txt
python manage.py migrate
python manage.py setup_pharmacy
python manage.py runserver
```

## النشر على السيرفر — `pweb.erpbylyomastech.com`

### 1) DNS
أضف سجل **A** للدومين يشير إلى IP السيرفر: `162.0.237.222`

### 2) على السيرفر (Ubuntu)

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nginx

# صلاحيات المجلد
sudo mkdir -p /var/www
sudo chown softwarehouse:softwarehouse /var/www

# تثبيت تلقائي
git clone https://github.com/Abdo-Nayel/Parma.git /var/www/parma
cd /var/www/parma
chmod +x deploy/install.sh
./deploy/install.sh
```

### 3) HTTPS (مُوصى به)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d pweb.erpbylyomastech.com
```

بعد SSL حدّث `.env`:

```
DJANGO_CSRF_TRUSTED_ORIGINS=https://pweb.erpbylyomastech.com
```

ثم: `sudo systemctl restart parma`

### 4) تحديث بعد تعديل الكود

```bash
cd /var/www/parma
git pull origin main
source venv/bin/activate
pip install -r Requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo systemctl restart parma
```

### أوامر مفيدة

| الأمر | الوظيفة |
|--------|---------|
| `sudo systemctl status parma` | حالة التطبيق |
| `sudo journalctl -u parma -f` | لوج الأخطاء |
| `tail -f /var/log/parma/error.log` | لوج Gunicorn |

## ملاحظات

- قاعدة البيانات SQLite في `pharmacy.db` — خذ نسخة احتياطية دورياً.
- الملفات المرفوعة في `media/` — لا تُرفع على Git.
- غيّر `DJANGO_SECRET_KEY` في `.env` على السيرفر.
