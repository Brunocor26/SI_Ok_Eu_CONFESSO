#!/usr/bin/env bash
# Inicia backend (Flask), frontend (Vite) e Mailpit em paralelo.
# Uso: ./start.sh
# Parar: Ctrl+C (termina todos os processos)

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/backend/.venv"

if [ ! -d "$VENV" ]; then
    echo -e "\033[0;31m[erro]\033[0m  Virtualenv não encontrado. Corre ./setup.sh primeiro."
    exit 1
fi

# ── Cores ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; RESET='\033[0m'

log()  { echo -e "${CYAN}[start]${RESET} $1"; }
ok()   { echo -e "${GREEN}[ok]${RESET}    $1"; }
warn() { echo -e "${YELLOW}[warn]${RESET}  $1"; }

cleanup() {
    echo ""
    log "A terminar todos os processos..."
    kill "$BACKEND_PID" "$FRONTEND_PID" "$MAILPIT_PID" 2>/dev/null
    wait 2>/dev/null
    log "Sistema parado."
}
trap cleanup EXIT INT TERM

# ── Mailpit ──────────────────────────────────────────────────────────────────
if command -v mailpit &>/dev/null; then
    log "A iniciar Mailpit (SMTP :1025 | UI :8025)..."
    mailpit &
    MAILPIT_PID=$!
    ok "Mailpit iniciado (PID $MAILPIT_PID)"
else
    warn "mailpit não encontrado — emails não serão entregues."
    warn "Instalar: https://mailpit.axllent.org/docs/install/"
    MAILPIT_PID=0
fi

# ── Backend ──────────────────────────────────────────────────────────────────
log "A iniciar Backend Flask em http://127.0.0.1:5000 ..."
cd "$ROOT/backend"
"$VENV/bin/flask" --app "app:create_app()" run --host=127.0.0.1 --port=5000 &
BACKEND_PID=$!
ok "Backend iniciado (PID $BACKEND_PID)"

# ── Frontend ─────────────────────────────────────────────────────────────────
log "A iniciar Frontend Vite em http://localhost:5173 ..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!
ok "Frontend iniciado (PID $FRONTEND_PID)"

# ── Pronto ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}  OK — Eu Confesso  |  Sistema iniciado${RESET}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "  Aplicação  →  ${CYAN}http://localhost:5173${RESET}"
echo -e "  Backend    →  ${CYAN}http://127.0.0.1:5000${RESET}"
echo -e "  Email UI   →  ${CYAN}http://localhost:8025${RESET}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "  Ctrl+C para parar tudo"
echo ""

wait
