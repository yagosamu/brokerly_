#!/usr/bin/env bash
set -euo pipefail

DUMP="${1:?informe o arquivo .dump}"
MEDIA_TAR="${2:-}"

if [[ "${3:-}" != "--yes" ]]; then
  echo "⚠ Isto vai DERRUBAR o schema atual. Use --yes para confirmar." >&2
  exit 1
fi

pg_restore --clean --if-exists --no-owner --no-privileges \
  -d "postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:${POSTGRES_PORT:-5432}/$POSTGRES_DB" \
  "$DUMP"

if [[ -n "$MEDIA_TAR" ]]; then
  rm -rf "${MEDIA_ROOT:-/app/media}"/*
  tar -xzf "$MEDIA_TAR" -C "${MEDIA_ROOT:-/app/media}/"
fi
