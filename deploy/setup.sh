#!/usr/bin/env bash
# ============================================================
# GateKeeper - Ubuntu 24.04 LTS Deployment Setup Script
# Run as root: sudo bash setup.sh
# ============================================================

set -euo pipefail

APP_USER="gatekeeper"
APP_DIR="/opt/gatekeeper"
PYTHON_BIN="python3"

echo "=== GateKeeper Deployment Setup ==="
echo ""

# Detect Python version
PYTHON_VERSION=$($PYTHON_BIN --version 2>&1 | awk '{print $2}')
echo "Detected Python: ${PYTHON_VERSION}"

# 1. System packages
echo ""
echo "[1/6] Installing system packages..."
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

# 2. Enable Apache modules
echo ""
echo "[2/6] Enabling Apache modules..."
a2enmod ssl headers wsgi expires rewrite
systemctl restart apache2

# 3. Create app user
echo ""
echo "[3/6] Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -m -s /bin/bash "$APP_USER"
    echo "User '${APP_USER}' created."
else
    echo "User '${APP_USER}' already exists."
fi

# 4. Application setup
echo ""
echo "[4/6] Setting up application..."

if [ ! -d "$APP_DIR" ]; then
    echo "ERROR: Application directory ${APP_DIR} not found!"
    echo ""
    echo "Please copy the GateKeeper files first:"
    echo "  mkdir -p ${APP_DIR}"
    echo "  cp -r /path/to/GateKeeper/* ${APP_DIR}/"
    echo "  chown -R ${APP_USER}:${APP_USER} ${APP_DIR}"
    echo ""
    echo "Then run this script again."
    exit 1
fi

chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

sudo -u "$APP_USER" bash -c "
    cd ${APP_DIR}
    ${PYTHON_BIN} -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
"
echo "Python dependencies installed."

# 5. Create .env file
echo ""
echo "[5/6] Creating .env file..."
SECRET_KEY=$($PYTHON_BIN -c "import secrets; print(secrets.token_hex(32))")
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
    echo ".env created. IMPORTANT: Change ADMIN_DEFAULT_PASSWORD!"
else
    echo ".env already exists, skipping."
fi

# Create instance directory for SQLite
mkdir -p "${APP_DIR}/instance"
chown "${APP_USER}:${APP_USER}" "${APP_DIR}/instance"

# Initialize the database
echo "Initializing database..."
sudo -u "$APP_USER" bash -c "
    cd ${APP_DIR}
    source venv/bin/activate
    ${PYTHON_BIN} -c 'from app import create_app; create_app(\"production\")'
"
echo "Database tables created."

# 6. Apache configuration
echo ""
echo "[6/6] Configuring Apache..."

APACHE_CONF="/etc/apache2/sites-available/gatekeeper.conf"
cat > "$APACHE_CONF" <<APACHEEOF
<VirtualHost *:80>
    ServerName _default_

    WSGIDaemonProcess gatekeeper \\
        python-home=/opt/gatekeeper/venv \\
        python-path=/opt/gatekeeper \\
        user=gatekeeper group=gatekeeper \\
        threads=5 processes=2

    WSGIProcessGroup gatekeeper
    WSGIScriptAlias / /opt/gatekeeper/wsgi.py

    Alias /static /opt/gatekeeper/app/static
    <Directory /opt/gatekeeper/app/static>
        Require all granted
    </Directory>

    <Directory /opt/gatekeeper>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-XSS-Protection "1; mode=block"

    SetEnv SECRET_KEY ${SECRET_KEY}
    SetEnv GATEKEEPER_ENV production

    ErrorLog \${APACHE_LOG_DIR}/gatekeeper_error.log
    CustomLog \${APACHE_LOG_DIR}/gatekeeper_access.log combined
</VirtualHost>
APACHEEOF

a2dissite 000-default 2>/dev/null || true
a2ensite gatekeeper
systemctl reload apache2
echo "Apache configured and reloaded."

echo ""
echo "============================================"
echo "  GateKeeper Setup Complete!"
echo "============================================"
echo ""
echo "  App URL:    http://$(hostname -I | awk '{print $1}')"
echo "  Admin URL:  http://$(hostname -I | awk '{print $1}')/admin/login"
echo "  Admin User: admin / admin"
echo ""
echo "  IMPORTANT next steps:"
echo "  1. Change admin password:"
echo "     cd ${APP_DIR} && source venv/bin/activate && flask seed-admin"
echo "  2. Replace logo: ${APP_DIR}/app/static/img/logo.png"
echo "  3. Optional - DSGVO cleanup cron:"
echo "     crontab -e"
echo "     0 2 * * * cd ${APP_DIR} && venv/bin/flask cleanup-visitors --days 90"
echo ""
