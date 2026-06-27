#!/bin/sh
set -e

python manage.py migrate --noinput --check || true

exec "$@"
