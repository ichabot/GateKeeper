# 🏢 GateKeeper

**Modern, iPad-optimized visitor management for company entrances.** Visitors check
themselves in and out on a kiosk; a password-protected admin area gives staff full
oversight, reporting, and GDPR tooling.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![Frontend](https://img.shields.io/badge/Frontend-Preact%20%2B%20htm%20(no%20build)-8b5cf6)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

### Kiosk (visitor self-service)
- **Guided check-in** — name, company, host, optional license plate, digital signature, GDPR consent.
- **Health questionnaire** — admin-configurable yes/no questions. Each question has an expected answer; a deviation blocks check-in.
- **PIN check-out** — a short PIN is issued at check-in; visitors check out on a touch numpad.
- **Returning-visitor pass ("Besucherausweis")** — opt-in. Stores only master data (never health answers) behind a QR token. On the next visit the kiosk scans it to pre-fill the form, and the visitor can **check out by scanning the pass** instead of typing the PIN.
- **Multi-language** — German, English, French, Spanish, switchable with one tap.
- **Info hub** — emergency contacts, directions, hygiene & safety pages, all editable in the admin area.
- **iPad-friendly** — screen Wake Lock keeps the display on, auto-return to the start screen after each action, camera QR scanning (over HTTPS) with a keyboard-wedge / manual fallback.

### Admin (password-protected)
- **Live view** — who is currently on site, with one-click check-out.
- **History** — filter by date range and free text; status column flags visitors the nightly job auto-closed as **"Not checked out"**.
- **Statistics** & **audit log** of admin-relevant actions.
- **Content editor** — info categories/pages and the health questionnaire, all four languages.
- **Settings** — SMTP/mail, branding (logo + accent colour), kiosk options, **admin accounts** (create / delete / reset password), and **GDPR** tools (unified search & delete of visits and passes, retention period).
- **Exports** — CSV (with per-question columns) and branded PDF history report.
- **Email** — instant emergency evacuation list and an automated monthly visitor report.
- **Automation** — nightly auto-checkout of forgotten visitors and automatic data cleanup after the configured retention period.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+ · Flask 3.x · Flask-SQLAlchemy · Flask-Login · Flask-WTF (CSRF) |
| Database | SQLite (file-based, no DB server) — schema changes applied automatically on startup |
| Frontend | **Preact + htm + native ES modules — no Node/Vite build step.** Libraries are vendored under `app/static/spa/vendor/` and resolved via an import map. |
| PDF / QR | reportlab · qrcode |
| App server | gunicorn behind a systemd service |
| TLS / exposure | your own reverse proxy (Caddy, nginx, Apache) — not installed by the setup script |

There is **no build pipeline**: the frontend ships as plain `.mjs`/`.css` files served
directly by Flask. Editing a frontend file and reloading the browser is all it takes.

---

## 🚀 Installation

> **Supported:** Ubuntu 22.04+ / Debian 12+.

### Production

`deploy/setup.sh` installs system packages, a Python venv, the database, cron jobs, and a
**gunicorn systemd service** listening on `127.0.0.1:8001`:

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/ichabot/GateKeeper.git /opt/gatekeeper
sudo bash /opt/gatekeeper/deploy/setup.sh
```

Then put a **reverse proxy** in front of `127.0.0.1:8001` to add HTTPS. An example Caddy
config is in [`deploy/Caddyfile.example`](deploy/Caddyfile.example) (nginx/Apache work too —
just `proxy_pass` to the same address). After enabling HTTPS, set `SESSION_COOKIE_SECURE=1`
in `/opt/gatekeeper/.env` and `sudo systemctl restart gatekeeper`.

```
Manage:  sudo systemctl {status|restart} gatekeeper
Logs:    sudo journalctl -u gatekeeper -f
```

### Development

```bash
sudo apt install -y python3 python3-venv python3-pip git
git clone https://github.com/ichabot/GateKeeper.git && cd GateKeeper
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask run
```

Dev server at **http://localhost:5000** (the SQLite DB is created automatically on startup).

### Default admin

Open the app and tap the **shield icon** (top-right) to sign in.

| | |
|---|---|
| Username | `admin` |
| Password | `admin` |

Change it immediately:

```bash
cd /opt/gatekeeper && source venv/bin/activate
flask seed-admin            # interactive / resets the admin password
```

…or create additional accounts in **Admin → Settings → Users**.

---

## 🔄 Upgrade

```bash
sudo bash /opt/gatekeeper/deploy/upgrade.sh
```

Pulls the latest code, updates dependencies, and restarts the service. Your **database,
`.env`, and uploaded logo are preserved**.

**Database migrations are automatic.** On startup the app factory runs `db.create_all()`
for new tables and idempotent `ALTER TABLE` steps for new columns, then backfills missing
seed data. No manual migration commands are needed.

Manual equivalent:

```bash
cd /opt/gatekeeper
sudo -u gatekeeper git pull origin main
sudo -u gatekeeper bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo systemctl restart gatekeeper
```

---

## ⌨️ CLI Commands

| Command | Description |
|---------|-------------|
| `flask run` | Start the development server |
| `flask seed-admin` | Create / reset the admin account |
| `flask cleanup-visitors [--days N]` | Delete visitor data older than N days (default: configured retention) — GDPR |
| `flask send-monthly-report` | Email the previous month's visitor CSV |
| `flask auto-checkout` | Auto-close visitors who forgot to check out (stamps 23:59:59 of the arrival day and flags them "not checked out") |

### Cron jobs

`deploy/setup.sh` installs these in `/etc/cron.d/gatekeeper`:

```cron
0 2 * * *  gatekeeper  cd /opt/gatekeeper && venv/bin/flask cleanup-visitors      # DSGVO cleanup, daily 02:00
0 7 1 * *  gatekeeper  cd /opt/gatekeeper && venv/bin/flask send-monthly-report   # monthly report, 1st @ 07:00
5 0 * * *  gatekeeper  cd /opt/gatekeeper && venv/bin/flask auto-checkout         # auto-checkout, daily 00:05
```

---

## 🔀 API (JSON)

Same-origin JSON API consumed by the SPA. Public endpoints are CSRF-exempt and
rate-limited; admin mutations require a `X-CSRFToken` header (fetched from `GET /api/csrf`).

**Public**

| Endpoint | Purpose |
|----------|---------|
| `GET /api/bootstrap` | Settings, health questions, info content |
| `POST /api/checkin` | Check in (accepts `save_profile`, `profile_token`; returns PIN + optional pass) |
| `POST /api/checkout` | Check out by **PIN or visitor-pass token** (`GKP:…`) |
| `POST /api/profile/lookup` | Resolve a pass token → master data for pre-fill |

**Admin** (login required)

`login/logout/session` · `visitors?scope=live|history&from&to&q` · `visitors/<id>/checkout` ·
`visitors/<id>` (DELETE) · `export/csv|pdf` · `stats` · `audit` · `info` · `health` ·
`settings` (+ `settings/logo`) · `users` (CRUD + password reset) · `profiles` (GDPR) ·
`emergency` · `smtp/test` · `content/export|import`.

Non-`/api` paths serve the SPA shell; `/uploads/<file>` serves the logo.

---

## 📁 Project Structure

```
GateKeeper/
├── app/
│   ├── __init__.py          # App factory: DB init, idempotent migrations, seeds, SPA serving, CLI
│   ├── extensions.py        # db, login_manager, csrf
│   ├── models.py            # SQLAlchemy models
│   ├── seed_content.py      # Default info categories, health questions, branding
│   ├── audit.py             # log_audit() → AuditLog
│   ├── mail.py              # SMTP: emergency list + monthly CSV report
│   ├── pdf.py               # Branded visitor PDF (reportlab)
│   ├── qr.py                # Scannable QR SVG
│   ├── content_io.py        # Editorial content export/import (JSON)
│   ├── api/                 # public.py (kiosk) + admin/ (authenticated) blueprints
│   └── static/spa/          # Preact+htm SPA — index.html, styles.css, vendor/, src/
│       └── src/             #   main, api, i18n, theme, ui, kiosk/, admin/…
├── deploy/
│   ├── setup.sh             # Production install (gunicorn + systemd)
│   ├── upgrade.sh           # Update an existing install
│   ├── gatekeeper.service   # systemd unit (reference)
│   └── Caddyfile.example    # Reverse-proxy example (not auto-installed)
├── database/schema.sql      # SQL schema reference (documentation only)
├── config.py                # Dev/Prod config
├── wsgi.py                  # WSGI entry point (application = create_app())
├── requirements.txt
└── .env.example
```

---

## 📱 iPad Kiosk Setup

1. Serve GateKeeper over **HTTPS** (needed for the screen Wake Lock and camera QR scanning).
2. Open the URL in Safari and **Add to Home Screen** for a fullscreen web app.
3. Enable **Guided Access** (Settings → Accessibility → Guided Access; triple-press the
   side button to lock the visitor into the app).

---

## 🔒 GDPR / Data Privacy

- Explicit consent is required before check-in; the signature is stored as a Base64 PNG.
- The returning-visitor pass stores **master data only — never health answers**.
- **Admin → Settings → Privacy**: one search finds and deletes both visit records and passes;
  the retention period drives automatic nightly cleanup.
- Editorial **export/import never includes** visitor data or the SMTP password.

---

## ⚠️ Disclaimer

Developed with AI assistance; uses third-party open-source dependencies that have **not been
independently audited**. Provided "as is" under the MIT License, without warranty.

- Personal/hobby project, not a certified visitor-management system.
- The sample health questions and safety texts are **examples** — adapt them to your regulations.
- Digital signatures are stored as Base64 PNG and are **not** qualified electronic signatures.
- Test thoroughly before production use.

---

## 📄 License

MIT License — see [LICENSE](LICENSE).
