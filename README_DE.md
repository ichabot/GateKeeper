# 🏢 GateKeeper

> 🇬🇧 [English Version](README.md)

**Modernes, iPad-optimiertes Besuchermanagement-System für den Einsatz am Firmeneingang. Besucher checken sich selbständig ein und aus, während ein passwortgeschützter Admin-Bereich die volle Übersicht bietet.**

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

- **Self-Service Check-in** — Vorname, Nachname, Firma, Ansprechpartner, KFZ-Kennzeichen, digitale Unterschrift, DSGVO-Einwilligung
- **Gesundheitsfragebogen** — 6 Ja/Nein-Fragen (Hygiene, Infektionskrankheiten)
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

```bash
# Repository klonen
git clone https://github.com/ichabot/GateKeeper.git
cd GateKeeper

# Virtual Environment erstellen und aktivieren
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# .env Datei anlegen
cp .env.example .env
# Optional: SECRET_KEY in .env anpassen

# Starten
flask run
```

Die App ist dann unter **http://localhost:5000** erreichbar.

> **Hinweis:** Die SQLite-Datenbank (`instance/gatekeeper.db`) wird automatisch beim ersten Start erstellt. Ein Admin-Benutzer (`admin` / `admin`) und die Standard-Infoseiten werden ebenfalls automatisch angelegt.

### Standard-Admin-Zugang

| | |
|---|---|
| URL | http://localhost:5000/admin/login |
| Benutzername | `admin` |
| Passwort | `admin` |

**Wichtig:** Passwort in Produktion ändern:

```bash
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
│   └── setup.sh                 # Ubuntu Deployment Script
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

## 🖥️ Deployment auf Ubuntu / Apache

### Schnellinstallation

```bash
# 1. Dateien auf den Server kopieren
sudo mkdir -p /opt/gatekeeper
sudo git clone https://github.com/ichabot/GateKeeper.git /opt/gatekeeper

# 2. Setup-Script ausführen
sudo bash /opt/gatekeeper/deploy/setup.sh
```

Das Script erledigt automatisch:
- System-Pakete installieren (Python3, Apache, mod_wsgi)
- Python Virtual Environment erstellen + Dependencies installieren
- `.env`-Datei mit generiertem Secret Key und SQLite-Pfad erstellen
- Datenbank-Tabellen anlegen + Admin-User + Standard-Seiten anlegen
- Apache konfigurieren und starten

### Manuelles Setup

1. **System-Pakete:**
   ```bash
   sudo apt-get update -y
   sudo apt-get install -y python3 python3-venv python3-dev \
       apache2 libapache2-mod-wsgi-py3
   ```

2. **App einrichten:**
   ```bash
   cd /opt/gatekeeper
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # .env anpassen: SECRET_KEY setzen
   # DATABASE_URL=sqlite:////opt/gatekeeper/instance/gatekeeper.db
   mkdir -p instance
   flask seed-admin --username admin
   ```

3. **Apache:**
   ```bash
   sudo a2enmod ssl headers wsgi expires
   sudo cp deploy/gatekeeper.conf /etc/apache2/sites-available/
   sudo a2dissite 000-default
   sudo a2ensite gatekeeper
   sudo systemctl reload apache2
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
