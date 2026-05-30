#!/usr/bin/env bash
# Instala dependências e inicializa a base de dados.
# Correr apenas uma vez antes do primeiro start.sh
# Uso: ./setup.sh

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/backend/.venv"

CYAN='\033[0;36m'; GREEN='\033[0;32m'; RESET='\033[0m'
log() { echo -e "${CYAN}[setup]${RESET} $1"; }
ok()  { echo -e "${GREEN}[ok]${RESET}    $1"; }

# ── Virtualenv ────────────────────────────────────────────────────────────────
if [ ! -d "$VENV" ]; then
    log "A criar virtualenv em backend/.venv ..."
    python3 -m venv "$VENV"
    ok "Virtualenv criado"
else
    ok "Virtualenv já existe — a saltar criação"
fi

# ── Backend ──────────────────────────────────────────────────────────────────
log "A instalar dependências Python..."
"$VENV/bin/pip" install -r "$ROOT/backend/requirements.txt" --quiet
ok "Dependências Python instaladas"

log "A inicializar base de dados..."
cd "$ROOT/backend"
"$VENV/bin/flask" --app "app:create_app()" db upgrade
ok "Base de dados pronta (instance/app.db)"

# ── Frontend ─────────────────────────────────────────────────────────────────
log "A instalar dependências Node..."
cd "$ROOT/frontend"
npm install --silent
ok "Dependências Node instaladas"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}  Setup concluído. Corre ./start.sh para iniciar.${RESET}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
