#!/bin/bash
# تثبيت كامل من الصفر — /var/www/pweb + PostgreSQL
# الاستخدام على السيرفر:
#   DB_PASSWORD='كلمة-قوية' bash deploy/install-pweb.sh
set -euo pipefail

APP_DIR="/var/www/pweb"
REPO="https://github.com/Abdo-Nayel/Parma.git"
DOMAIN="pweb.erpbylyomastech.com"
DB_NAME="${DB_NAME:-pweb}"
DB_USER="${DB_USER:-pweb}"
DB_PASSWORD="${DB_PASSWORD:-}"

if [ -z "$DB_PASSWORD" ]; then
  echo "مطلوب: DB_PASSWORD='كلمة-قوية' bash deploy/install-pweb.sh"
  exit 1
fi

echo "==> إيقاف الخدمة"
sudo systemctl stop pweb 2>/dev/null || true

echo "==> PostgreSQL"
sudo apt-get update -qq
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql

echo "==> مجلدات التطبيق"
sudo mkdir -p /var/log/pweb
sudo rm -rf "$APP_DIR"
sudo mkdir -p "$APP_DIR"
sudo chown -R softwarehouse:www-data "$APP_DIR" /var/log/pweb

echo "==> استنساخ المشروع"
git clone "$REPO" "$APP_DIR"
cd "$APP_DIR"
chmod +x deploy/setup-postgres.sh

export DB_NAME DB_USER DB_PASSWORD
bash deploy/setup-postgres.sh

echo "==> Python venv"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r Requirements.txt

echo "==> .env"
SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
cat > .env <<ENV
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=${SECRET}
DJANGO_ALLOWED_HOSTS=${DOMAIN},162.0.237.222
DJANGO_CSRF_TRUSTED_ORIGINS=https://${DOMAIN}
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True

DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=127.0.0.1
DB_PORT=5432
ENV

echo "==> migrate + static + admin"
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py setup_pharmacy

echo "==> systemd + nginx"
sudo cp deploy/pweb.service /etc/systemd/system/pweb.service
sudo systemctl daemon-reload
sudo systemctl enable pweb
sudo systemctl restart pweb

sudo cp deploy/nginx-pweb.conf /etc/nginx/sites-available/pweb
sudo ln -sf /etc/nginx/sites-available/pweb /etc/nginx/sites-enabled/pweb
sudo nginx -t
sudo systemctl reload nginx

echo ""
echo "تم التثبيت بنجاح."
echo "الموقع: https://${DOMAIN}"
echo "الدخول: admin / admin123  (غيّر كلمة المرور فوراً)"
echo "حالة الخدمة: sudo systemctl status pweb"
echo ""
echo "HTTPS (لو مش مفعّل):"
echo "  sudo certbot --nginx -d ${DOMAIN}"
