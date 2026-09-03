#!/usr/bin/env bash
# Deploy script: sincroniza el proyecto a la VPS y despliega el contenedor Docker.
# Uso:
#   ./deploy.sh            # rsync + rebuild completo (cambios en deps/Dockerfile)
#   ./deploy.sh fast       # solo rsync + restart api (cambios en .py; evita rebuild)
set -euo pipefail

REMOTE="${REMOTE:-blackdaysvps}"
DEST="${DEST:-/var/www/html/bot}"
LOCAL="$(cd "$(dirname "$0")" && pwd)"

EXCLUDES=(
  --exclude='.venv' --exclude='venv' --exclude='__pycache__' --exclude='*.pyc'
  --exclude='Model/config.env' --exclude='.env' --exclude='responses/' --exclude='*.session'
)

echo "==> rsync $LOCAL -> $REMOTE:$DEST"
rsync -azcP "${EXCLUDES[@]}" "$LOCAL"/ "$REMOTE:$DEST"/ >&2

if [[ "${1:-}" == "fast" ]]; then
  echo "==> fast mode: restart api"
  ssh "$REMOTE" "cd $DEST && docker compose restart api"
else
  echo "==> rebuild + up"
  ssh "$REMOTE" "cd $DEST && docker compose up -d --build"
fi

sleep 3
echo "==> health"
ssh "$REMOTE" "curl -s -m 10 http://localhost:8080/apis/health; echo"