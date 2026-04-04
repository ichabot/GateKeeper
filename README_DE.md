# 🏢 GateKeeper

> 🇬🇧 [English Version](README.md)

**Modernes, iPad-optimiertes Besuchermanagement-System für den Einsatz am Firmeneingang. Besucher checken sich selbständig ein und aus, während ein passwortgeschützter Admin-Bereich die volle Übersicht bietet.**

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📸 Screenshots

| Home | Check-in | Admin Dashboard |
|------|----------|------------------|
| ![Home](docs/screenshots/home.png) | ![Check-in](docs/screenshots/checkin.png) | ![Dashboard](docs/screenshots/admin-dashboard.png) |

---

## ✨ Features

- **Self-Service Check-in** — Vorname, Nachname, Firma, Ansprechpartner, KFZ-Kennzeichen, digitale Unterschrift, DSGVO-Einwilligung
- **Gesundheitsfragebogen** — Dynamische Ja/Nein-Fragen, im Admin-Bereich konfigurierbar (Hygiene, Infektionskrankheiten)
- **Hygieneregeln & Sicherheitshinweise** — Verlinkbare Unterseiten mit Einwilligungs-Checkboxen
- **4-stelliger PIN** — Wird beim Check-in generiert, damit checkt der Besucher beim Gehen wieder aus
- **Touch-optimiertes Unterschriftenfeld** — Finger / Apple Pencil Support
- **Visuelles PIN-Numpad** — Für den Check-out (kein Keyboard nötig)
- **Seitenmenü** — Notfallkontakte, Notfallpläne, Notrufnummern, Besucherinformationen, Hygieneregeln, Sicherheitshinweise
- **Admin-Dashboard** (passwortgeschützt):
  - Besucherliste mit Filter (Datum, Status, Freitextsuche)
  - Anzeige der Unterschriften und Fragebogen-Antworten
  - CSV-Export (inkl. Fragebogen-Spalten)
  - Statische Seiten bearbeiten (Notfall-Infos, Hygieneregeln, Sicherheitshinweise etc.)
  - SMTP-Einstellungen für automatischen monatlichen Besucherbericht per E-Mail
- **Monatlicher E-Mail-Report** — Besucherliste als CSV-Anhang, automatisch per Cronjob oder manuell aus dem Admin-Bereich
- **Notfall-Evakuierungsliste** — Aktuelle Besucherliste sofort per E-Mail an Notfall-Empfänger senden
- **Zweisprachig** — Deutsch / Englisch (umschaltbar per Klick)
- **DSGVO-konform** — Einwilligungs-Checkbox, automatischer Daten-Cleanup
- **iPad-Kiosk-optimiert** — Meta-Tags, touch-freundliche UI, Auto-Redirect nach Aktionen

---

## ⚠️ Hinweis / Haftungsausschluss

Dieses Projekt wurde mit KI-Unterstützung entwickelt („Vibe Coding") und nutzt Open-Source-Bibliotheken von Drittanbietern, die **nicht unabhängig geprüft** wurden. Die Software wird „wie besehen" unter der MIT-Lizenz bereitgestellt, ohne jegliche Gewährleistung.

**Bitte beachten:**
- Dieses Tool ist ein privates Hobby-Projekt, kein zertifiziertes Besuchermanagementsystem
- Der Gesundheitsfragebogen und die Sicherheitshinweise sind **Beispiele** — passe sie an deine spezifischen Vorschriften an
- Digitale Unterschriften werden als Base64-PNG gespeichert — nicht in allen Rechtsordnungen gleichwertig mit qualifizierten elektronischen Signaturen
- Externe Abhängigkeiten (Flask, SQLAlchemy, Pico CSS etc.) werden von ihren jeweiligen Projekten gepflegt
- Vor dem Einsatz in einer Produktionsumgebung immer gründlich testen

> **Kurzfassung:** Erst testen, Inhalte an eigene Bedürfnisse anpassen, Konformität mit lokalen Vorschriften prüfen.

---

## 🛠️ Tech Stack

| Komponente | Technologie |
|------------|-------------|
| Backend | Python 3.11+ / Flask 3.x |
| Datenbank | SQLite (dateibasiert, kein Server nötig) |
| ORM | SQLAlchemy + Flask-Migrate |
| Frontend | Pico CSS v2 + Vanilla JS |
| Auth | Flask-Login + Werkzeug Password Hashing |
| i18n | Deutsch / Englisch (Session-basiert) |
| Deployment | Apache + mod_wsgi oder Gunicorn |

---

## 📋 Voraussetzungen

| Komponente | Version | Hinweis |
|------------|---------|---------|
| **Python** | 3.11+ | Empfohlen: 3.12 |
| **pip** | aktuell | Oder [uv](https://docs.astral.sh/uv/) verwenden |

---

## 🚀 Installation

> **Hinweis:** GateKeeper läuft unter Linux (Ubuntu 22.04+ / Debian 12+). Windows wird nicht unterstützt.

### Produktiv-Deployment (empfohlen)

Ein Befehl installiert alles — System-Pakete, Apache, Python-Dependencies, Datenbank, Cron-Jobs:

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/ichabot/GateKeeper.git /opt/gatekeeper
sudo bash /opt/gatekeeper/deploy/setup.sh
```

Die App ist dann unter **http://deine-server-ip** (Port 80) erreichbar.

Alternativ kann das Setup-Script direkt ohne vorheriges Klonen ausgeführt werden:

```bash
curl -sL https://raw.githubusercontent.com/ichabot/GateKeeper/main/deploy/setup.sh | sudo bash
```

### Entwicklung (lokales Testen)

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

Der Entwicklungsserver ist dann unter **http://localhost:5000** erreichbar (nur lokaler Zugriff).

### Standard-Admin-Zugang

| | |
|---|---|
| URL | `http://deine-server-ip/admin/login` |
| Benutzername | `admin` |
| Passwort | `admin` |

**Wichtig:** Passwort nach dem Setup ändern:

```bash
cd /opt/gatekeeper && source venv/bin/activate
flask seed-admin --username admin --password <neues-passwort>
```

---

## 📁 Projektstruktur

```
GateKeeper/
├── app/
│   ├── __init__.py              # App Factory, CLI Commands, Seed-Daten
│   ├── extensions.py            # Flask Extensions (DB, Login, Babel, CSRF)
│   ├── models.py                # Datenmodelle (Visitor, AdminUser, StaticPage, SmtpSettings)
│   ├── mail.py                  # E-Mail-Versand (SMTP, monatlicher CSV-Report)
│   ├── visitor/                 # Blueprint: Besucher-Seiten
│   │   ├── routes.py            #   Check-in, Check-out, Info-Seiten, Sprache
│   │   └── forms.py             #   WTForms (CheckIn, CheckOut)
│   ├── admin/                   # Blueprint: Admin-Bereich
│   │   ├── routes.py            #   Login, Dashboard, Export, Seitenverwaltung, SMTP
│   │   └── forms.py             #   WTForms (Login, Filter, EditPage, SmtpSettings)
│   ├── templates/               # Jinja2 Templates
│   │   ├── base.html            #   Master-Layout (Header, Nav, Footer)
│   │   ├── visitor/             #   Home, Checkin, Checkout, Info, Success
│   │   └── admin/               #   Login, Dashboard, Seitenverwaltung
│   ├── static/
│   │   ├── css/style.css        #   Custom Styles (Pico CSS Basis)
│   │   ├── js/app.js            #   PIN-Numpad, Signature Pad, Auto-Timeout
│   │   └── img/logo.png         #   Firmenlogo (Platzhalter — bitte ersetzen)
│   └── translations/            # Flask-Babel Übersetzungsdateien
├── deploy/
│   ├── gatekeeper.conf          # Apache VHost Konfiguration (Referenz)
│   ├── setup.sh                 # Produktiv-Deployment Script
│   └── upgrade.sh               # Bestehende Installation aktualisieren
├── database/
│   └── schema.sql               # SQL Schema Referenz (Dokumentation)
├── config.py                    # Flask Config (Development / Production)
├── wsgi.py                      # WSGI Entry Point für Apache / Gunicorn
├── requirements.txt             # Python Dependencies
├── babel.cfg                    # Flask-Babel Extraktions-Config
└── .env.example                 # Umgebungsvariablen Vorlage
```

---

## 🔀 Routen-Übersicht

### Besucher (öffentlich)

| Route | Beschreibung |
|-------|-------------|
| `GET /` | Willkommensseite (Einchecken / Auschecken) |
| `GET/POST /checkin` | Check-in Formular |
| `GET /checkin/success/<pin>` | PIN-Anzeige nach Check-in |
| `GET/POST /checkout` | Check-out per PIN-Numpad |
| `GET /checkout/success` | Verabschiedung |
| `GET /info/<slug>` | Statische Info-Seiten |
| `GET /lang/<code>` | Sprache wechseln (de/en) |

### Admin (passwortgeschützt)

| Route | Beschreibung |
|-------|-------------|
| `GET/POST /admin/login` | Admin-Login |
| `GET /admin/logout` | Abmelden |
| `GET /admin/dashboard` | Besucher-Dashboard mit Filtern |
| `GET /admin/export` | CSV-Export (gefiltert, inkl. Fragebogen) |
| `GET /admin/pages` | Statische Seiten verwalten |
| `GET/POST /admin/pages/<slug>` | Seite bearbeiten (HTML) |
| `GET/POST /admin/smtp` | SMTP-Einstellungen für E-Mail-Report |
| `POST /admin/smtp/test` | Test-E-Mail senden (aktueller Monat) |
| `POST /admin/smtp/send-report` | Vormonatsbericht manuell senden |
| `POST /admin/emergency-send` | Notfall-Evakuierungsliste senden |

---

## 🖥️ Was das Setup-Script macht

Das `deploy/setup.sh` führt folgende Schritte aus:

1. System-Pakete installieren (Python3, Apache2, mod_wsgi, git)
2. Eigenen `gatekeeper` System-Benutzer anlegen
3. Repository nach `/opt/gatekeeper` klonen (oder vorhandene Dateien nutzen)
4. Python Virtual Environment erstellen + Dependencies installieren
5. `.env`-Datei mit zufälligem SECRET_KEY + SQLite-Pfad generieren
6. Datenbank initialisieren (Tabellen, Admin-User, Seed-Daten)
7. Apache VirtualHost auf Port 80 konfigurieren
8. Cron-Jobs installieren (DSGVO-Cleanup + monatlicher E-Mail-Report)

Nach dem Setup läuft Apache mit GateKeeper automatisch — auch nach einem Neustart.

---

## 🔄 Upgrade

Um eine bestehende Installation auf die neueste Version zu aktualisieren:

```bash
sudo bash /opt/gatekeeper/deploy/upgrade.sh
```

Das Script holt den neuesten Code, aktualisiert Dependencies und startet Apache neu. Datenbank, `.env`-Konfiguration und Logo bleiben erhalten.

**Manuelles Upgrade** (gleiche Schritte):

```bash
cd /opt/gatekeeper
sudo -u gatekeeper git pull origin main
sudo -u gatekeeper bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo systemctl restart apache2
```

---

## 📱 iPad-Kiosk Einrichtung

1. Safari öffnen und die GateKeeper-URL aufrufen
2. "Zum Home-Bildschirm" hinzufügen (für Vollbild-Webapp)
3. **Geführter Zugang** (Guided Access) aktivieren:
   - Einstellungen > Bedienungshilfen > Geführter Zugang
   - Dreimal Home-/Seitentaste drücken zum Aktivieren
   - Verhindert, dass Besucher die App verlassen

---

## 🎨 Anpassung

### Firmenlogo

Das Platzhalter-Logo unter `app/static/img/logo.png` durch das eigene Firmenlogo ersetzen. Empfohlene Größe: max. 160px Breite, 40px Höhe, PNG mit transparentem Hintergrund.

### Titeltext ändern

Alle Textstellen befinden sich in `app/templates/base.html`:

| Element | Standard |
|---------|---------|
| `<span class="app-title">` | `GateKeeper` |
| `{% block title %}` | `GateKeeper` |
| Footer-Text | `GateKeeper © 2026 — Besuchermanagement` |

### Statische Seiten

Inhalte der Infoseiten (Hygieneregeln, Sicherheitshinweise etc.) können direkt im Admin-Bereich unter "Seiten" bearbeitet werden — kein Code-Zugriff nötig.

---

## ⌨️ CLI Commands

| Command | Beschreibung |
|---------|-------------|
| `flask run` | Entwicklungsserver starten |
| `flask seed-admin` | Admin-Benutzer erstellen/Passwort ändern |
| `flask cleanup-visitors --days 90` | Alte Besucherdaten löschen (DSGVO) |
| `flask send-monthly-report` | Vormonatsbericht per E-Mail senden |

---

## 🔒 DSGVO / Datenschutz

- Besucher müssen vor dem Check-in der Datenschutzerklärung zustimmen
- Unterschrift wird digital erfasst und gespeichert
- Besucher können **keine** Daten anderer Besucher einsehen
- Automatischer Daten-Cleanup per Cronjob:

```bash
# Täglicher Cleanup (Daten älter als 90 Tage)
0 2 * * * cd /opt/gatekeeper && venv/bin/flask cleanup-visitors --days 90
```

---

## 📧 E-Mail Report

### Monatlicher Besucherbericht

Am 1. jeden Monats um 7:00 Uhr den Vormonatsbericht senden:

```bash
0 7 1 * * cd /opt/gatekeeper && venv/bin/flask send-monthly-report
```

### Einrichtung

1. Admin-Dashboard öffnen → **E-Mail / SMTP**
2. SMTP-Zugangsdaten eintragen
3. **Test-E-Mail senden** zum Prüfen der Verbindung
4. **Monatlicher Versand aktiv** aktivieren

---

## 📄 Lizenz

MIT License — siehe [LICENSE](LICENSE)
