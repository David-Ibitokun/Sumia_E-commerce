#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

if [ "${DJANGO_SEED_DB:-false}" = "true" ]; then
    echo "--> DJANGO_SEED_DB is true: Seeding database..."
    python seed_db.py
else
    echo "--> Skipping database seeding (set DJANGO_SEED_DB=true to populate starter data)."
fi

