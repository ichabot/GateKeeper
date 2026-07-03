#!/usr/bin/env bash
# ============================================================
# GateKeeper - Production Deployment Script
# Supported: Ubuntu 22.04 / 24.04 LTS, Debian 12+
#
# Serves the app with gunicorn behind a systemd service on
# 127.0.0.1:8001. TLS and public exposure are handled by YOUR
# own reverse proxy (Caddy, nginx, Apache) — see deploy/Caddyfile.example.
#
# Usage (as root):
#   sudo bash deploy/setup.sh
#
# Or one-shot:
#   curl -sL https://raw.githubusercontent.com/ichabot/GateKeeper/main/deploy/setup.sh | sudo bash
# ============================================================

set -euo pipefail

APP_USER="gatekeeper"
APP_DIR="/opt/gatekeeper"
REPO_URL="https://github.com/ichabot/GateKeeper.git"
PYTHON_BIN="python3"
BIND_ADDR="127.0.0.1:8001"   # gunicorn listens here; your proxy forwards to it

echo ""
echo "============================================"
echo "  GateKeeper - Production Setup (gunicorn)"
echo "============================================"
echo ""

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: This script must be run as root (sudo bash setup.sh)"
    exit 1
fi

# --------------------------------------------------------
# 1. System packages
# --------------------------------------------------------
echo "[1/6] Installing system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv python3-dev python3-pip git

PYTHON_VERSION=$($PYTHON_BIN --version 2>&1 | awk '{print $2}')
echo "  Python: ${PYTHON_VERSION}"

# --------------------------------------------------------
# 2. Application user
# --------------------------------------------------------
echo ""
echo "[2/6] Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -m -s /bin/bash "$APP_USER"
    echo "  User '${APP_USER}' created."
else
    echo "  User '${APP_USER}' already exists."
fi

# --------------------------------------------------------
# 3. Application files
# --------------------------------------------------------
echo ""
echo "[3/6] Setting up application files..."
if [ -d "${APP_DIR}/.git" ]; then
    echo "  Repository exists, pulling latest changes..."
    cd "$APP_DIR"
    sudo -u "$APP_USER" git pull origin main 2>/dev/null || echo "  (git pull skipped - using existing files)"
elif [ -d "$APP_DIR" ]; then
    echo "  Application directory exists (not a git repo), using existing files."
else
    echo "  Cloning repository..."
    git clone "$REPO_URL" "$APP_DIR"
fi
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

# --------------------------------------------------------
# 4. Python virtual environment + dependencies
# --------------------------------------------------------
echo ""
echo "[4/6] Installing Python dependencies (incl. gunicorn)..."
sudo -u "$APP_USER" bash -c "
    cd ${APP_DIR}
    ${PYTHON_BIN} -m venv venv
    source venv/bin/activate
    pip install --upgrade pip >/dev/null 2>&1
    pip install -r requirements.txt >/dev/null 2>&1
"
echo "  Dependencies installed."

# --------------------------------------------------------
# 5. Environment + database
# --------------------------------------------------------
echo ""
echo "[5/6] Configuring environment..."
SECRET_KEY=$(${PYTHON_BIN} -c "import secrets; print(secrets.token_hex(32))")
ENV_FILE="${APP_DIR}/.env"

if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<ENVEOF
FLASK_APP=wsgi.py
GATEKEEPER_ENV=production
SECRET_KEY=${SECRET_KEY}
ADMIN_DEFAULT_PASSWORD=admin
DATABASE_URL=sqlite:////opt/gatekeeper/instance/gatekeeper.db
# Set to 1 once the app is served over HTTPS (also required for the iPad Wake Lock):
SESSION_COOKIE_SECURE=0
ENVEOF
    chown "${APP_USER}:${APP_USER}" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "  .env created with a generated SECRET_KEY."
else
    echo "  .env already exists, keeping existing configuration."
fi

mkdir -p "${APP_DIR}/instance"
chown "${APP_USER}:${APP_USER}" "${APP_DIR}/instance"

echo "  Initializing database (tables + default admin + seed data)..."
sudo -u "$APP_USER" bash -c "
    cd ${APP_DIR}
    source venv/bin/activate
    ${PYTHON_BIN} -c 'from app import create_app; create_app(\"production\")'
" 2>/dev/null
echo "  Database ready."

# --------------------------------------------------------
# 6. systemd service (gunicorn)
# --------------------------------------------------------
echo ""
echo "[6/6] Installing systemd service..."
SERVICE_FILE="/etc/systemd/system/gatekeeper.service"
cat > "$SERVICE_FILE" <<UNITEOF
[Unit]
Description=GateKeeper visitor management (gunicorn)
After=network.target

[Service]
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/gunicorn --workers 3 --bind ${BIND_ADDR} --timeout 60 wsgi:application
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
UNITEOF

systemctl daemon-reload
systemctl enable gatekeeper >/dev/null 2>&1
systemctl restart gatekeeper
echo "  Service 'gatekeeper' enabled and started (listening on ${BIND_ADDR})."

# --------------------------------------------------------
# Cron jobs (DSGVO cleanup, monthly report, auto-checkout)
# --------------------------------------------------------
CRON_FILE="/etc/cron.d/gatekeeper"
if [ ! -f "$CRON_FILE" ]; then
    cat > "$CRON_FILE" <<'CRONEOF'
# GateKeeper - automated tasks (flask reads .env itself)
SHELL=/bin/bash

# DSGVO: delete visitor data older than the configured retention (daily 2:00 AM)
0 2 * * * gatekeeper cd /opt/gatekeeper && venv/bin/flask cleanup-visitors >/dev/null 2>&1

# Monthly visitor report via email (1st of month at 7:00 AM)
0 7 1 * * gatekeeper cd /opt/gatekeeper && venv/bin/flask send-monthly-report >/dev/null 2>&1

# Auto-checkout visitors who forgot to check out (daily at 0:05 AM)
5 0 * * * gatekeeper cd /opt/gatekeeper && venv/bin/flask auto-checkout >/dev/null 2>&1
CRONEOF
    chmod 644 "$CRON_FILE"
    echo "  Cron jobs installed (/etc/cron.d/gatekeeper)."
fi

# --------------------------------------------------------
# Done!
# --------------------------------------------------------
echo ""
echo "============================================"
echo "  GateKeeper Setup Complete!"
echo "============================================"
echo ""
echo "  App (internal):  http://${BIND_ADDR}   (gunicorn)"
echo "  Admin:           open the app, tap the shield icon (top-right) to sign in"
echo "  Admin login:     admin / admin  --  CHANGE THIS"
echo ""
echo "  NEXT: put a reverse proxy in front of ${BIND_ADDR} to add HTTPS."
echo "        See deploy/Caddyfile.example. Then set SESSION_COOKIE_SECURE=1"
echo "        in ${APP_DIR}/.env and 'systemctl restart gatekeeper'."
echo ""
echo "  Manage:  systemctl {status|restart} gatekeeper"
echo "  Logs:    journalctl -u gatekeeper -f"
echo "  Files:   App ${APP_DIR}/  |  DB ${APP_DIR}/instance/gatekeeper.db  |  Config ${APP_DIR}/.env"
echo ""
