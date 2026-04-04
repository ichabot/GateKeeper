# CLAUDE.md - GateKeeper Projektinfo für KI-Assistenten

## Projektüberblick

GateKeeper ist ein iPad-optimiertes Besuchermanagement-System (Flask / Python).
Besucher checken sich am Firmeneingang selbst ein und aus.

## Technologie

- **Backend**: Python 3.11+, Flask 3.x, Flask-WTF, Flask-Login, Flask-Babel
- **Datenbank**: SQLite (dateibasiert via SQLAlchemy) - **kein PostgreSQL**
- **Frontend**: Pico CSS v2, Vanilla JavaScript (kein Framework)
- **Deployment**: Apache + mod_wsgi auf Ubuntu

## Datenbankpfade

- Entwicklung: `instance/gatekeeper.db` (automatisch, relativ zum App-Root)
- Produktion: `/opt/gatekeeper/instance/gatekeeper.db` (absoluter Pfad in .env)
- SQLite-URI-Format (4 Slashes = absoluter Pfad): `sqlite:////opt/gatekeeper/instance/gatekeeper.db`

## Projektstruktur (wichtige Dateien)

```
app/
  __init__.py        - App Factory + CLI-Befehle + _seed_defaults() für DB-Startdaten
  models.py          - SQLAlchemy-Models: Visitor, AdminUser, StaticPage, SmtpSettings
  extensions.py      - Flask-Extensions (db, migrate, login_manager, babel, csrf)
  mail.py            - SMTP-Versand: monatlicher CSV-Report + Notfall-Evakuierungsliste
  visitor/
    routes.py        - Besucher-Routen (checkin, checkout, info_page, set_language)
    forms.py         - WTForms: CheckInForm, CheckOutForm (health questions are dynamic, not in form)
  admin/
    routes.py        - Admin-Routen (dashboard, export, pages, smtp, emergency-send)
    forms.py         - WTForms: LoginForm, FilterForm, EditPageForm, SmtpSettingsForm
  templates/
    base.html        - Master-Layout mit Sidebar (Breite: 400px), Header, Footer
    visitor/
      checkin.html   - Check-in-Formular (Personaldaten, Gesundheitsfragebogen,
                       Unterschrift, 3 Consent-Checkboxen)
      checkout.html  - PIN-Numpad
      info_page.html - Generisches Template für statische Seiten
  static/
    css/style.css    - Custom CSS (Pico CSS Basis), Cacheversion: ?v=8
    js/app.js        - Sidebar, PIN-Pad, Signature-Pad, Countdown, Draft-Persistence
config.py            - Dev/Prod Config (beide mit SQLite-Default)
deploy/setup.sh      - Ubuntu-Deployment-Script (kein PostgreSQL)
database/schema.sql  - SQL-Schema als Dokumentation (nicht direkt ausgeführt)
```

## Visitor-Model (alle Felder)

```
id, first_name, last_name, company, contact_person
license_plate (String 20, nullable - KFZ-Kennzeichen, optional)
pin (4 Zeichen, eindeutig unter aktiven Besuchern)
arrival_time, departure_time (nullable = noch vor Ort)
signature_data (Base64-PNG als Text)
dsgvo_consent, hygiene_consent, safety_consent (Boolean)
q1_flu, q2_diarrhea, q3_food_poisoning, q4_parasites, q5_ent, q6_skin (Boolean, nullable)
created_at
```

## Statische Seiten (StaticPage-Model)

Werden über `/info/<slug>` aufgerufen und im Admin bearbeitet.
Beim ersten Start automatisch geseeded (in `_seed_defaults()`):

| Slug | DE | EN |
|------|----|---|
| emergency_contacts | Kontakte | Contacts |
| emergency_plans | Notfallpläne | Emergency Plans |
| emergency_numbers | Notrufnummern | Emergency Numbers |
| visitor_info | Besucherinformationen | Visitor Information |
| hygiene_rules | Hygieneregeln | Hygiene Rules |
| safety_conduct | Sicherheits-/Verhaltenshinweise | Rules of safety / conduct |

## Mehrsprachigkeit

- Kein Flask-Babel gettext — stattdessen direkte Jinja2-Ternaries:
  `{{ "Deutsch" if lang == 'de' else "English" }}`
- Sprachauswahl via `session['lang']` (default: 'de')
- `{% set lang = session.get('lang', 'de') %}` am Anfang jedes Templates

## Check-in-Formular Ablauf

1. Personaldaten (Vorname, Nachname, Firma, Ansprechpartner, KFZ-Kennzeichen)
2. Gesundheitsfragebogen (dynamische Ja/Nein-Fragen aus DB, via request.form)
3. Unterschrift (Canvas, Base64-PNG, via JS/fetch übermittelt)
4. DSGVO-Checkbox (öffnet Modal)
5. Hygiene-Checkbox (Link zu `/info/hygiene_rules`, target=_blank)
6. Safety-Checkbox (Link zu `/info/safety_conduct`, target=_blank)
7. Submit (via fetch, wegen Signature-Data)

## JavaScript (app.js)

- `toggleSideNav()` / `closeSideNav()` — Sidebar
- `numpadPress()` / `numpadClear()` — PIN-Eingabe (Checkout)
- `initSignaturePad()` — Canvas-Zeichenfläche (iPad-Touch + Maus)
- `startCountdown(seconds, url)` — Auto-Redirect auf Success-Seiten
- `saveCheckinDraft()` / `restoreCheckinDraft()` — localStorage-Persistenz
- Form-Submit via `fetch()` um Signature-Data mitzuschicken

## Coding-Konventionen

- **SQLite only** — keine PostgreSQL-abhängigen Features (Arrays, JSON-Operators etc.)
- Umgebungsvariable: `GATEKEEPER_ENV` (nicht FLASK_ENV, deprecated seit Flask 2.3)
- Production-Modus verweigert Start ohne SECRET_KEY
- Checkout-PIN hat Rate-Limiting (10 Versuche / 2 Min pro IP)
- Signatur-Daten max. 500KB Base64
- CSV-Export mit UTF-8 BOM-Prefix für Excel-Kompatibilität
- Neue Formularfelder immer in forms.py, models.py UND routes.py hinzufügen
- Neue statische Seiten in `_seed_defaults()` in `__init__.py` eintragen
- CSS-Cache-Version in base.html hochzählen wenn style.css geändert wird (?v=N)
- Gleich für app.js
- Alle User-facing Texte zweisprachig (DE/EN) im Template
- `.gitattributes` normalisiert alle Zeilenumbrüche automatisch auf LF
