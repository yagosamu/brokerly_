#!/usr/bin/env bash
set -euo pipefail

TS=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_DIR:-/var/backups/brokerly}"

mkdir -p "$BACKUP_DIR"

echo "[+] Dump PostgreSQL"
pg_dump --no-owner --no-privileges --format=custom \
  --file="$BACKUP_DIR/db_$TS.dump" \
  "postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:${POSTGRES_PORT:-5432}/$POSTGRES_DB"

echo "[+] Tarball de media"
tar -czf "$BACKUP_DIR/media_$TS.tar.gz" -C "${MEDIA_ROOT:-/app/media}" .

echo "[+] Concluído em $BACKUP_DIR"
