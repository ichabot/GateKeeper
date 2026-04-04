#!/usr/bin/env bash
# ============================================================
# GateKeeper - Production Deployment Script
# Supported: Ubuntu 22.04 / 24.04 LTS, Debian 12+
#
# Usage (as root):
#   curl -sL https://raw.githubusercontent.com/ichabot/GateKeeper/main/deploy/setup.sh | sudo bash
#
# Or after cloning:
#   sudo bash deploy/setup.sh
# ============================================================

set -euo pipefail

APP_USER="gatekeeper"
APP_DIR="/opt/gatekeeper"
REPO_URL="https://github.com/ichabot/GateKeeper.git"
PYTHON_BIN="python3"

echo ""
echo "============================================"
echo "  GateKeeper - Production Setup"
echo "============================================"
echo ""

# Check root
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: This script must be run as root (sudo bash setup.sh)"
    exit 1
fi

# --------------------------------------------------------
# 1. System packages
# --------------------------------------------------------
echo "[1/7] Installing system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    apache2 \
    libapache2-mod-wsgi-py3 \
    git

PYTHON_VERSION=$($PYTHON_BIN --version 2>&1 | awk '{print $2}')
echo "  Python: ${PYTHON_VERSION}"

# --------------------------------------------------------
# 2. Enable Apache modules
# --------------------------------------------------------
echo ""
echo "[2/7] Enabling Apache modules..."
a2enmod headers wsgi expires rewrite >/dev/null 2>&1
systemctl restart apache2

# --------------------------------------------------------
# 3. Create application user
# --------------------------------------------------------
echo ""
echo "[3/7] Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -m -s /bin/bash "$APP_USER"
    echo "  User '${APP_USER}' created."
else
    echo "  User '${APP_USER}' already exists."
fi

# --------------------------------------------------------
# 4. Clone or update repository
# --------------------------------------------------------
echo ""
echo "[4/7] Setting up application files..."
if [ -d "${APP_DIR}/.git" ]; then
    echo "  Repository exists, pulling latest changes..."
    cd "$APP_DIR"
    git pull origin main 2>/dev/null || echo "  (git pull skipped - using existing files)"
elif [ -d "$APP_DIR" ] && [ ! -d "${APP_DIR}/.git" ]; then
    # Directory exists but isn't a git repo (manual copy)
    echo "  Application directory exists (not a git repo), using existing files."
else
    echo "  Cloning repository..."
    git clone "$REPO_URL" "$APP_DIR"
fi

chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

# --------------------------------------------------------
# 5. Python virtual environment + dependencies
# --------------------------------------------------------
echo ""
echo "[5/7] Installing Python dependencies..."
sudo -u "$APP_USER" bash -c "
    cd ${APP_DIR}
    ${PYTHON_BIN} -m venv venv
    source venv/bin/activate
    pip install --upgrade pip >/dev/null 2>&1
    pip install -r requirements.txt >/dev/null 2>&1
"
echo "  Dependencies installed."

# --------------------------------------------------------
# 6. Environment configuration + database
# --------------------------------------------------------
echo ""
echo "[6/7] Configuring environment..."
SECRET_KEY=$(${PYTHON_BIN} -c "import secrets; print(secrets.token_hex(32))")
ENV_FILE="${APP_DIR}/.env"

if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<ENVEOF
FLASK_APP=wsgi.py
GATEKEEPER_ENV=production
SECRET_KEY=${SECRET_KEY}
ADMIN_DEFAULT_PASSWORD=admin
DATABASE_URL=sqlite:////opt/gatekeeper/instance/gatekeeper.db
ENVEOF
    chown "${APP_USER}:${APP_USER}" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "  .env created with generated SECRET_KEY."
else
    echo "  .env already exists, keeping existing configuration."
fi

# Create instance directory for SQLite database
mkdir -p "${APP_DIR}/instance"
chown "${APP_USER}:${APP_USER}" "${APP_DIR}/instance"

# Initialize database (creates tables + default admin user + seed data)
echo "  Initializing database..."
sudo -u "$APP_USER" bash -c "
    cd ${APP_DIR}
    source venv/bin/activate
    ${PYTHON_BIN} -c 'from app import create_app; create_app(\"production\")'
" 2>/dev/null
echo "  Database ready."

# --------------------------------------------------------
# 7. Apache configuration
# --------------------------------------------------------
echo ""
echo "[7/7] Configuring Apache..."

APACHE_CONF="/etc/apache2/sites-available/gatekeeper.conf"
cat > "$APACHE_CONF" <<'APACHEEOF'
<VirtualHost *:80>
    ServerName _default_

    WSGIDaemonProcess gatekeeper \
        python-home=/opt/gatekeeper/venv \
        python-path=/opt/gatekeeper \
        user=gatekeeper group=gatekeeper \
        threads=5 processes=2

    WSGIProcessGroup gatekeeper
    WSGIScriptAlias / /opt/gatekeeper/wsgi.py

    Alias /static /opt/gatekeeper/app/static
    <Directory /opt/gatekeeper/app/static>
        Require all granted
        ExpiresActive On
        ExpiresByType image/png "access plus 1 month"
        ExpiresByType text/css "access plus 1 week"
        ExpiresByType application/javascript "access plus 1 week"
    </Directory>

    <Directory /opt/gatekeeper>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"

    ErrorLog ${APACHE_LOG_DIR}/gatekeeper_error.log
    CustomLog ${APACHE_LOG_DIR}/gatekeeper_access.log combined
</VirtualHost>
APACHEEOF

# Pass environment variables to Apache
APACHE_ENVVARS="/etc/apache2/envvars"
if ! grep -q "GATEKEEPER_ENV" "$APACHE_ENVVARS" 2>/dev/null; then
    echo "" >> "$APACHE_ENVVARS"
    echo "# GateKeeper environment" >> "$APACHE_ENVVARS"
    echo "export GATEKEEPER_ENV=production" >> "$APACHE_ENVVARS"
    echo "export SECRET_KEY=${SECRET_KEY}" >> "$APACHE_ENVVARS"
    echo "export DATABASE_URL=sqlite:////opt/gatekeeper/instance/gatekeeper.db" >> "$APACHE_ENVVARS"
fi

a2dissite 000-default >/dev/null 2>&1 || true
a2ensite gatekeeper >/dev/null 2>&1
systemctl reload apache2
echo "  Apache configured and running."

# --------------------------------------------------------
# Optional: Cron jobs for DSGVO cleanup + monthly report
# --------------------------------------------------------
CRON_FILE="/etc/cron.d/gatekeeper"
if [ ! -f "$CRON_FILE" ]; then
    cat > "$CRON_FILE" <<'CRONEOF'
# GateKeeper - automated tasks
SHELL=/bin/bash
FLASK_APP=wsgi.py
GATEKEEPER_ENV=production

# DSGVO: delete visitor data older than 90 days (daily at 2:00 AM)
0 2 * * * gatekeeper cd /opt/gatekeeper && venv/bin/flask cleanup-visitors --days 90

# Monthly visitor report via email (1st of month at 7:00 AM)
0 7 1 * * gatekeeper cd /opt/gatekeeper && venv/bin/flask send-monthly-report

CRONEOF
    chmod 644 "$CRON_FILE"
    echo ""
    echo "  Cron jobs installed (/etc/cron.d/gatekeeper):"
    echo "    - DSGVO cleanup: daily at 2:00 AM (90 days)"
    echo "    - Monthly report: 1st of month at 7:00 AM"
fi

# --------------------------------------------------------
# Done!
# --------------------------------------------------------
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "============================================"
echo "  GateKeeper Setup Complete!"
echo "============================================"
echo ""
echo "  App URL:    http://${SERVER_IP}"
echo "  Admin URL:  http://${SERVER_IP}/admin/login"
echo "  Admin User: admin / admin"
echo ""
echo "  IMPORTANT next steps:"
echo "  1. Change admin password:"
echo "     cd ${APP_DIR} && source venv/bin/activate && flask seed-admin"
echo "  2. Replace logo: ${APP_DIR}/app/static/img/logo.png"
echo "  3. Configure SMTP in admin area for email reports"
echo ""
echo "  Files:"
echo "    App:      ${APP_DIR}/"
echo "    Database: ${APP_DIR}/instance/gatekeeper.db"
echo "    Config:   ${APP_DIR}/.env"
echo "    Apache:   /etc/apache2/sites-available/gatekeeper.conf"
echo "    Cron:     /etc/cron.d/gatekeeper"
echo "    Logs:     /var/log/apache2/gatekeeper_*.log"
echo ""
echo "  Service management:"
echo "    sudo systemctl restart apache2   # Restart"
echo "    sudo systemctl status apache2    # Status"
echo "    sudo tail -f /var/log/apache2/gatekeeper_error.log  # Errors"
echo ""
