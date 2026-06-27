#!/bin/bash
# تحديث سريع على السيرفر بعد git pull
set -euo pipefail

APP_DIR="/var/www/pweb"
cd "$APP_DIR"

echo "==> git pull"
git pull origin main

echo "==> dependencies"
source venv/bin/activate
pip install -r Requirements.txt

echo "==> migrate + collectstatic"
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

echo "==> restart"
sudo systemctl restart pweb
sudo systemctl reload nginx

echo "تم التحديث. امسح كاش المتصفح (Ctrl+Shift+R) لو الشكل لسه قديم."
