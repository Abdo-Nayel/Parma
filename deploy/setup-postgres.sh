#!/bin/bash
# إعداد قاعدة PostgreSQL لمشروع pweb — شغّله مرة واحدة على السيرفر
set -euo pipefail

DB_NAME="${DB_NAME:-pweb}"
DB_USER="${DB_USER:-pweb}"
DB_PASSWORD="${DB_PASSWORD:-}"

if [ -z "$DB_PASSWORD" ]; then
  echo "استخدم: DB_PASSWORD='كلمة-قوية' bash deploy/setup-postgres.sh"
  exit 1
fi

echo "==> إنشاء مستخدم وقاعدة بيانات PostgreSQL"
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
    CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
  ELSE
    ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
  END IF;
END
\$\$;

SELECT 'CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}')\gexec

GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
SQL

echo "==> تم: DB=${DB_NAME} USER=${DB_USER}"
