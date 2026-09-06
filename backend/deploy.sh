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
  echo "==> fast mode: restart api (recarga módulos .py bind-mounteados)"
  ssh "$REMOTE" "cd $DEST && docker compose up -d --force-recreate --no-build api"
else
  echo "==> rebuild + recreate"
  # --force-recreate garantiza nuevo proceso Python: el código viaja por bind
  # mount (/app) y sin recreate-app un up -d no detecta cambios de .py ni recarga
  # los módulos ya importados en memoria.
  ssh "$REMOTE" "cd $DEST && docker compose up -d --build --force-recreate"
fi

sleep 3
echo "==> health"
ssh "$REMOTE" "curl -s -m 10 http://localhost:8080/apis/health; echo"