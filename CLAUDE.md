# CLAUDE.md — GateKeeper Projektinfo für KI-Assistenten

## Projektüberblick

GateKeeper ist ein iPad-optimiertes Besuchermanagement-System. Besucher checken
sich am Firmeneingang selbst ein und aus. **Redesign 2026:** komplett neu als
**React-SPA (Preact + htm, ohne Build-Schritt) + Flask-JSON-API**. Die alten
Jinja-Templates und HTML-Blueprints wurden entfernt.

Planungsdokumente: `REBUILD-PLAN.md` und `INFOS-NICHT-UPLOADEN/ANALYSE-Prototyp.md`
(letzterer Ordner ist gitignored).

## Technologie

- **Backend**: Python 3.11+, Flask 3.x, Flask-SQLAlchemy, Flask-Login, Flask-WTF (CSRF), reportlab (PDF), qrcode (SVG).
- **Datenbank**: SQLite (dateibasiert). **Kein PostgreSQL.**
- **Frontend**: Preact + htm + native ES-Module — **kein Node/Vite-Build**. Bibliotheken sind unter `app/static/spa/vendor/` vendored und werden per Import-Map aufgelöst.
- **Deployment**: gunicorn als systemd-Service `gatekeeper` (Bind `127.0.0.1:8001`), installiert von `deploy/setup.sh`. TLS/Reverse-Proxy macht der Betreiber selbst (in Prod: Caddy, manuell — **nicht** in `setup.sh`).

## Projektstruktur

```
app/
  __init__.py        App-Factory: DB-Init, idempotente Migrationen, Seeds,
                     StaticPage→Markdown-Migration, SPA-Serving, CLI-Befehle.
  extensions.py      db, migrate, login_manager, csrf (babel ungenutzt).
  models.py          SQLAlchemy-Modelle (siehe unten).
  seed_content.py    Default-Inhalte (Info-Kategorien, Health-Intro/-Fragen, Branding).
  audit.py           log_audit(action, detail) → AuditLog.
  mail.py            SMTP: Notfall-Liste + monatlicher CSV-Report.
  pdf.py             build_visitor_pdf() — gebrandeter Verlaufs-Report (reportlab).
  qr.py              qr_svg() — echter, scannbarer QR-Code als SVG.
  content_io.py      export_content()/import_content() — redaktionelle Inhalte als JSON.
  api/
    __init__.py      register_api(app, csrf); Serializer (visitor_to_dict, settings_public, iso).
    public.py        /api/bootstrap, /api/checkin, /api/checkout, /api/csrf (CSRF-exempt).
    admin/…          admin.py: /api/admin/* (login, visitors, stats, audit, info,
                     health, settings, logo, emergency, smtp/test, content export/import).
  static/
    spa/
      index.html     SPA-Shell (Import-Map, Google-Fonts, styles.css, main.mjs).
      styles.css     Design-Tokens + Komponenten-CSS.
      vendor/        preact.mjs, hooks.mjs, htm.mjs (vendored, kein CDN zur Laufzeit).
      src/
        main.mjs     App-Wurzel: lädt /api/bootstrap, Routing kiosk/admin, Toast.
        api.mjs      fetch-Wrapper (apiGet/apiPost/... ) inkl. X-CSRFToken-Header.
        i18n.mjs     I18N (DE/EN/FR/ES), tt(lang), pick(obj,lang).
        theme.mjs    PALETTES (5 Akzente) + freier Hex-Akzent, applyAccent(), backdropFor().
        wakeLock.mjs iPad wach halten (Screen Wake Lock API + Re-Acquire).
        markdown.mjs blocksOf() — "## Überschrift" + Absätze.
        format.mjs   Datums-/Dauer-Formatierung (locale).
        ui.mjs       html-Binding (htm), Icon, Modal, Toast, StepDots, Field.
        kiosk/index.mjs   Kompletter Kiosk-Flow.
        admin/*.mjs       index (Shell/Login/KPIs) + live/history/stats/audit/info/health/settings.
config.py            Dev/Prod-Config (+ UPLOAD_FOLDER, MAX_CONTENT_LENGTH, CSRF, Cookies).
deploy/setup.sh      Ubuntu-Deployment (gunicorn+systemd, Cron, kein Node); gatekeeper.service + Caddyfile.example als Referenz.
```

## Datenmodell (models.py)

- **Visitor**: first_name, last_name, company, contact_person, license_plate (opt),
  pin (String), arrival_time/departure_time (UTC), signature_data (Base64-PNG),
  dsgvo/hygiene/safety_consent, profile_token (opt — verknüpft den Besuch mit dem
  beim Check-in genutzten/erstellten Besucherausweis, ermöglicht Check-out per Ausweis),
  auto_checked_out (Bool — vom nächtlichen `auto-checkout` gesetzt = „vergessen auszuchecken",
  Anzeige als Badge „Nicht ausgecheckt"), `generate_unique_pin()`,
  `missed_checkout`-Property (noch offen & Ankunft vor heute). Legacy q1..q6 nur noch für Altdaten.
- **HealthQuestion**: position, text_de/en/fr/es, short_key (unique), active,
  **correct_answer (Bool)** — Sollantwort; Abweichung blockt Check-in. `to_dict()`.
- **VisitorAnswer**: visitor_id, question_id, answer (Bool).
- **AdminUser**: username (unique), password_hash (Werkzeug).
- **SmtpSettings**: Single-Row id=1 (Host/Port/User/Passwort/Absender/Empfänger, use_tls, enabled).
- **AppSettings**: Single-Row id=1 — company_name, logo_path, accent, retention_days,
  kiosk_backdrop, collect_plate, auto_return_seconds, health_intro_de/en/fr/es.
- **AuditLog**: created_at, action (Code), detail, user, ip.
- **InfoCategory**: key, type ('dir'|'art'), icon, accent, position, title_*, body_*
  (Markdown, für 'art'), entries_json ([{label:{..},value}], für 'dir'). `to_dict()`, `entries`-Property.
- **VisitorProfile**: Opt-in Wiederkehrer-„Besucherausweis". token (unique, 10 Zeichen
  aus eindeutigem Alphabet), Stammdaten (first/last/company/contact_person/plate),
  created_at/last_seen_at. **Nie Gesundheitsdaten.** `generate_token()`, `to_dict()`.
  Verfällt per `cleanup-visitors` nach Inaktivität (last_seen_at < retention).
- **StaticPage**: DEPRECATED — nur noch Migrationsquelle, wird nicht mehr gelesen.

## API (JSON)

Öffentlich (CSRF-exempt, rate-limitiert):
`GET /api/csrf` · `GET /api/bootstrap` · `POST /api/checkin` · `POST /api/checkout` ·
`POST /api/profile/lookup` (Besucherausweis-Token → Stammdaten für Vorausfüllung).
`POST /api/checkin` akzeptiert `save_profile` (bool) + `profile_token` (bei Wiederkommen)
und liefert bei Profil `pass_token` + `pass_qr` zurück.
`POST /api/checkout` nimmt `code` (oder `pin`): rein numerisch → PIN, sonst (bzw. mit
`GKP:`-Prefix) → Besucherausweis-Token; sucht den passenden aktiven Besuch und checkt aus.

Admin (Login nötig, Mutationen brauchen `X-CSRFToken`-Header):
`POST /api/admin/login|logout` · `GET /api/admin/session` ·
`GET /api/admin/visitors?scope=live|history&from&to&q` ·
`POST /api/admin/visitors/<id>/checkout` · `DELETE /api/admin/visitors/<id>` ·
`GET /api/admin/visitors/<id>/signature` ·
`GET /api/admin/export/csv|pdf` · `GET /api/admin/stats` · `GET /api/admin/audit` ·
`GET /api/admin/info` · `PUT /api/admin/info/<key>` ·
`GET /api/admin/profiles?q=` · `DELETE /api/admin/profiles/<id>` (DSGVO) ·
`GET /api/admin/users` · `POST /api/admin/users` (Konto anlegen) ·
`PUT /api/admin/users/<id>/password` (PW zurücksetzen) · `DELETE /api/admin/users/<id>`
(Selbstlöschung & letztes Konto serverseitig verhindert) ·
`GET|PUT /api/admin/health` · `GET|PUT /api/admin/settings` ·
`POST|DELETE /api/admin/settings/logo` · `POST /api/admin/emergency` · `POST /api/admin/smtp/test` ·
`GET /api/admin/content/export` · `POST /api/admin/content/import?mode=replace|fill&preview=0|1`.

Nicht-`/api`-Pfade liefern die SPA-Shell (`/` + Catch-all). `/uploads/<file>` liefert das Logo.

## Wichtige Konventionen / Fallstricke

- **ES-Module-MIME**: `.mjs` muss als `text/javascript` ausgeliefert werden, sonst
  blockiert der Browser die Module. Serverseitig gesetzt via `mimetypes.add_type`
  (Flask). gunicorn liefert die statischen Dateien direkt über Flask aus.
- **htm-Syntax**: Komponenten schließen mit `<//>`, Interpolation `<${Comp} .../>`.
- **i18n**: Statische UI-Texte liegen komplett in `i18n.mjs`. Dynamische Inhalte
  (Fragen, Info, Branding) kommen in allen 4 Sprachen vom Server; Client wählt via `pick()`.
- **Auth/CSRF**: Same-Origin, Flask-Login-Session-Cookie (`SameSite=Lax`, HttpOnly).
  Admin-Mutationen: Token von `GET /api/csrf` → Header `X-CSRFToken`. `api.mjs` macht das automatisch.
- **HTTPS/Wake-Lock**: Der iPad-Screen-Wake-Lock braucht HTTPS (über den Reverse-Proxy)
  und `SESSION_COOKIE_SECURE=1`. Ohne HTTPS Guided Access am iPad nutzen.
- **Besucherausweis (Wiederkommen)**: QR enthält nur den Token (`GKP:<token>`), das
  Besucher-Handy braucht **kein Netz** — der Kiosk liest den QR. Kamera-Scan (`src/scan.mjs`,
  vendored `vendor/jsqr.js`) braucht Secure-Context (**HTTPS**); ohne HTTPS greift automatisch
  das Code-Feld (Keyboard-Wedge-Scanner tippt rein / manuell). Profil ist Opt-in + DSGVO-löschbar.
- **Zeitzonen**: Speicherung UTC, Anzeige Europe/Berlin (`to_berlin()` im Backend,
  `toLocale*` im Frontend). `BERLIN_TZ` in `app/__init__.py`.
- **Fragebogen-Logik**: Check-in blockt, wenn eine Antwort ≠ `correct_answer`
  (Default `False` = „Nein" ist korrekt → verhaltensgleich zum alten „jedes Ja blockt").
- **Export/Import**: enthält Info + Fragebogen + Branding (+ Logo als Base64). **Nie**
  Besucherdaten oder SMTP-Passwort. Import-Modi „replace" / „fill".
- **SQLite only** — keine PG-spezifischen Features. `GATEKEEPER_ENV` statt FLASK_ENV.
  Production verweigert Start ohne SECRET_KEY.
- **Uploads** liegen in `instance/uploads/` (überleben Updates). CSV mit UTF-8-BOM.

## Migration von der Altversion

`create_app()` ist idempotent: `db.create_all()` legt neue Tabellen an,
`_run_migrations()` ergänzt fehlende Spalten (u. a. `correct_answer`) per ALTER,
`_seed_defaults()` seedt AppSettings/InfoCategory und übernimmt admin-editierte
`StaticPage`-Inhalte (HTML→Markdown) in die passenden `art`-Kategorien.

## CLI (Cron)

`flask seed-admin` · `flask cleanup-visitors [--days N]` (Default: AppSettings.retention_days) ·
`flask send-monthly-report` · `flask auto-checkout` (nachts 00:05: offene Besuche von
Vortagen → Check-out auf 23:59:59 des Ankunftstags + `auto_checked_out=True`).
