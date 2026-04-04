#!/usr/bin/env bash
# ============================================================
# GateKeeper - Upgrade Script
# Updates an existing installation to the latest version.
#
# Usage (as root):
#   sudo bash /opt/gatekeeper/deploy/upgrade.sh
# ============================================================

set -euo pipefail

APP_DIR="/opt/gatekeeper"
APP_USER="gatekeeper"

echo ""
echo "============================================"
echo "  GateKeeper - Upgrade"
echo "============================================"
echo ""

# Check root
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: This script must be run as root (sudo bash upgrade.sh)"
    exit 1
fi

# Check installation
if [ ! -d "${APP_DIR}/.git" ]; then
    echo "ERROR: No GateKeeper installation found at ${APP_DIR}"
    echo "       Run deploy/setup.sh first for a fresh installation."
    exit 1
fi

cd "$APP_DIR"

# Show current version
CURRENT=$(git rev-parse --short HEAD)
echo "  Current version: ${CURRENT}"

# 1. Pull latest code
echo ""
echo "[1/3] Pulling latest changes..."
sudo -u "$APP_USER" git pull origin main
NEW=$(git rev-parse --short HEAD)

if [ "$CURRENT" = "$NEW" ]; then
    echo "  Already up to date (${CURRENT})."
    echo ""
    exit 0
fi

echo "  Updated: ${CURRENT} -> ${NEW}"

# 2. Update Python dependencies
echo ""
echo "[2/3] Updating Python dependencies..."
sudo -u "$APP_USER" bash -c "
    cd ${APP_DIR}
    source venv/bin/activate
    pip install --upgrade pip >/dev/null 2>&1
    pip install -r requirements.txt >/dev/null 2>&1
"
echo "  Dependencies updated."

# 3. Restart Apache
echo ""
echo "[3/3] Restarting Apache..."
systemctl restart apache2
echo "  Apache restarted."

# Done
echo ""
echo "============================================"
echo "  Upgrade Complete!  ${CURRENT} -> ${NEW}"
echo "============================================"
echo ""
echo "  Changes:"
git log --oneline "${CURRENT}..${NEW}" | sed 's/^/    /'
echo ""
