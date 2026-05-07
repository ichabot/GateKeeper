# 🏢 GateKeeper

**Modern, iPad-optimized visitor management system for company entrances. Visitors check themselves in and out, while a password-protected admin area provides full oversight.**

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📸 Screenshots

| Home | Check-in | Admin Dashboard |
|------|----------|-----------------|
| ![Home](docs/screenshots/home.png) | ![Check-in](docs/screenshots/checkin.png) | ![Dashboard](docs/screenshots/admin-dashboard.png) |

---

## ✨ Features

- **Self-service check-in** — Name, company, contact person, license plate, digital signature, GDPR consent
- **Health questionnaire** — Dynamic yes/no questions, configurable in admin area
- **4-digit PIN checkout** — Generated at check-in, touch-optimized numpad
- **Digital signature** — Canvas with finger / Apple Pencil support
- **Multi-language** — German, English, French, Spanish (switchable with one click)
- **Side menu** — Emergency contacts, plans, numbers, visitor info, hygiene rules, safety instructions
- **Admin dashboard** (password-protected):
  - Visitor list with filters (date, status, text search)
  - Signature and questionnaire answer display
  - CSV export (with dynamic questionnaire columns)
  - Edit static pages (emergency info, hygiene rules, safety instructions)
  - SMTP settings for automatic monthly visitor reports
  - Health question management (add/edit/delete, all 4 languages)
- **Monthly email report** — Visitor CSV via cron or manual trigger
- **Emergency evacuation list** — Instant email to emergency contacts
- **Nightly auto-checkout** — Visitors who forgot to check out are auto-closed at midnight
- **GDPR compliant** — Consent checkbox, automatic data cleanup (configurable retention period)
- **iPad kiosk optimized** — Meta tags, touch-friendly UI, auto-redirect after actions

---

## ⚠️ Disclaimer

This project was developed with AI assistance and uses third-party open-source dependencies that have **not been independently audited**. The software is provided "as is" under the MIT License, without warranty of any kind.

- This is a personal/hobby project, not a certified visitor management system
- Health questionnaire and safety instructions are **examples** — adapt to your regulations
- Digital signatures are stored as Base64 PNG — not legally equivalent to qualified electronic signatures
- Always test thoroughly before deploying in a production environment

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+ / Flask 3.x |
| Database | SQLite (file-based, no server needed) |
| ORM | SQLAlchemy + Flask-Migrate |
| Frontend | Pico CSS v2 + Vanilla JS |
| Auth | Flask-Login + Werkzeug Password Hashing |
| i18n | DE / EN / FR / ES (session-based, no gettext) |
| Deployment | Apache + mod_wsgi (Ubuntu/Debian) |

---

## 🚀 Installation

> **Supported:** Ubuntu 22.04+ / Debian 12+. Windows is not supported.

### Production Deployment (recommended)

One command installs everything — system packages, Apache, Python dependencies, database, cron jobs:

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/ichabot/GateKeeper.git /opt/gatekeeper
sudo bash /opt/gatekeeper/deploy/setup.sh
```

The app is then available at **http://your-server-ip** (port 80).

Alternatively, run the setup script directly:

```bash
curl -sL https://raw.githubusercontent.com/ichabot/GateKeeper/main/deploy/setup.sh | sudo bash
```

### Development (local testing)

```bash
sudo apt install -y python3 python3-venv python3-pip git

git clone https://github.com/ichabot/GateKeeper.git
cd GateKeeper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask run
```

Dev server at **http://localhost:5000**.

### Default Admin Access

| | |
|---|---|
| URL | `http://your-server-ip/admin/login` |
| Username | `admin` |
| Password | `admin` |

**Change the password immediately:**

```bash
cd /opt/gatekeeper && source venv/bin/activate
flask seed-admin --username admin --password <new-password>
```

---

## 🔄 Upgrade

To update an existing installation to the latest version:

```bash
sudo bash /opt/gatekeeper/deploy/upgrade.sh
```

This pulls the latest code, updates dependencies, and restarts Apache. Your **database, `.env` configuration, and logo are preserved**.

### Database Migrations

GateKeeper uses SQLite and handles schema changes **automatically on startup**:

- New columns (e.g. French/Spanish translations) are added via `ALTER TABLE` on first request after upgrade
- Default seed data (health questions, static pages) is backfilled with missing translations
- No manual migration commands needed — just upgrade and restart

### Manual Upgrade

```bash
cd /opt/gatekeeper
sudo -u gatekeeper git pull origin main
sudo -u gatekeeper bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo systemctl restart apache2
```

### Upgrading from v1.0.0 to v1.1.0

The v1.1.0 release adds French/Spanish support and several bugfixes. After upgrading:

1. **Database schema** — New columns (`text_fr`, `text_es`, `title_fr`, `title_es`, `content_fr`, `content_es`) are added automatically on first request
2. **Seed data** — French/Spanish translations for default health questions and static pages are backfilled automatically
3. **Cron jobs** — A new `auto-checkout` command was added. Update your cron file:
   ```bash
   # Add to /etc/cron.d/gatekeeper:
   5 0 * * * gatekeeper cd /opt/gatekeeper && venv/bin/flask auto-checkout
   ```
4. **No data loss** — All existing visitor records, admin settings, and custom page content are preserved

---

## ⌨️ CLI Commands

| Command | Description |
|---------|-------------|
| `flask run` | Start development server |
| `flask seed-admin` | Create/reset admin user password |
| `flask cleanup-visitors --days 90` | Delete old visitor data (GDPR) |
| `flask send-monthly-report` | Send previous month's report by email |
| `flask auto-checkout` | Auto-checkout visitors from previous days |

---

## 📁 Project Structure

```
GateKeeper/
├── app/
│   ├── __init__.py              # App Factory, CLI Commands, Seed Data, DB Migrations
│   ├── extensions.py            # Flask Extensions (DB, Login, Babel, CSRF)
│   ├── models.py                # Data Models (Visitor, AdminUser, StaticPage, SmtpSettings, HealthQuestion)
│   ├── mail.py                  # Email Sending (SMTP, monthly CSV report, emergency list)
│   ├── translations.py          # UI string translations (DE/EN/FR/ES)
│   ├── visitor/                 # Blueprint: Visitor Pages
│   │   ├── routes.py            #   Check-in, Check-out, Info Pages, Language Switch
│   │   └── forms.py             #   WTForms (CheckIn, CheckOut)
│   ├── admin/                   # Blueprint: Admin Area
│   │   ├── routes.py            #   Login, Dashboard, Export, Pages, SMTP, Questions
│   │   └── forms.py             #   WTForms (Login, Filter, EditPage, SmtpSettings, HealthQuestion)
│   ├── templates/               # Jinja2 Templates
│   │   ├── base.html            #   Master Layout (Header, Sidebar, Footer, Lang Switcher)
│   │   ├── visitor/             #   Home, Checkin, Checkout, Info, Success
│   │   └── admin/               #   Login, Dashboard, Pages, Questions, SMTP
│   └── static/
│       ├── css/style.css        #   Custom Styles (Pico CSS base)
│       ├── js/app.js            #   PIN Numpad, Signature Pad, Auto-Timeout
│       └── img/logo.png         #   Company Logo (replace with yours)
├── deploy/
│   ├── setup.sh                 # Production Deployment Script
│   ├── upgrade.sh               # Upgrade Existing Installation
│   └── gatekeeper.conf          # Apache VHost Configuration (reference)
├── database/
│   └── schema.sql               # SQL Schema Reference (documentation only)
├── config.py                    # Flask Config (Development / Production)
├── wsgi.py                      # WSGI Entry Point
├── requirements.txt             # Python Dependencies
└── .env.example                 # Environment Variables Template
```

---

## 🔀 Routes

### Visitor (public)

| Route | Description |
|-------|-------------|
| `GET /` | Welcome page (Check-in / Check-out) |
| `GET/POST /checkin` | Check-in form |
| `GET /checkin/success/<pin>` | PIN display after check-in |
| `GET/POST /checkout` | Check-out via PIN numpad |
| `GET /checkout/success` | Farewell page |
| `GET /info/<slug>` | Static info pages |
| `GET /lang/<code>` | Switch language (de/en/fr/es) |

### Admin (password-protected)

| Route | Description |
|-------|-------------|
| `GET/POST /admin/login` | Admin login |
| `GET /admin/logout` | Logout |
| `GET /admin/dashboard` | Visitor dashboard with filters |
| `GET /admin/export` | CSV export (filtered) |
| `GET /admin/pages` | Manage static pages |
| `GET/POST /admin/pages/<slug>` | Edit page content (DE/EN/FR/ES, HTML) |
| `GET /admin/questions` | Health question management |
| `GET/POST /admin/questions/new` | Create new question |
| `GET/POST /admin/questions/<id>` | Edit question |
| `GET/POST /admin/smtp` | SMTP / email settings |
| `POST /admin/smtp/test` | Send test email |
| `POST /admin/smtp/send-report` | Send previous month's report |
| `POST /admin/emergency-send` | Send emergency evacuation list |

---

## 📱 iPad Kiosk Setup

1. Open Safari and navigate to the GateKeeper URL
2. **Add to Home Screen** (for fullscreen webapp)
3. Enable **Guided Access**:
   - Settings → Accessibility → Guided Access
   - Triple-press Home/Side button to activate
   - Prevents visitors from leaving the app

---

## 🎨 Customization

### Company Logo

Replace `app/static/img/logo.png` with your logo (max 160×40px, PNG, transparent background).

### Static Pages

All info page content (hygiene rules, safety instructions, emergency info) can be edited in the admin area under **Manage Pages** — no code changes needed. Each page supports DE/EN/FR/ES.

### Health Questions

Add, edit, reorder, or deactivate health questionnaire questions in the admin area. Each question supports all 4 languages.

---

## 🔒 GDPR / Data Privacy

- Visitors must consent to the privacy policy before check-in
- Digital signature captured and stored (Base64 PNG)
- Visitors cannot view other visitors' data
- Automatic data cleanup via cron (see [Cron Jobs](#-cron-jobs) below)

---

## 📧 Cron Jobs

The setup script installs these automatically in `/etc/cron.d/gatekeeper`:

```bash
# GDPR cleanup: delete records older than 90 days (daily 2:00 AM)
0 2 * * * gatekeeper cd /opt/gatekeeper && venv/bin/flask cleanup-visitors --days 90

# Auto-checkout: close missed visitors from previous days (daily 0:05 AM)
5 0 * * * gatekeeper cd /opt/gatekeeper && venv/bin/flask auto-checkout

# Monthly email report: 1st of month at 7:00 AM
0 7 1 * * gatekeeper cd /opt/gatekeeper && venv/bin/flask send-monthly-report
```

### SMTP Setup

1. Admin Dashboard → **Email / SMTP**
2. Enter SMTP credentials
3. **Send test email** to verify
4. Enable **Monthly sending active**

---

## 📄 License

MIT License — see [LICENSE](LICENSE)
