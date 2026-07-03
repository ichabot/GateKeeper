# GateKeeper Redesign — Detailplan (Umbau auf React-SPA + Flask-JSON-API)

> Grundlage: `INFOS-NICHT-UPLOADEN/ANALYSE-Prototyp.md`. Stand: 2026-07-02.
> Entscheidungen des Users bereits bestätigt (siehe §0).

## 0. Bestätigte Entscheidungen

| # | Thema | Entscheidung |
|---|---|---|
| 1 | Besucher-Name | **Getrennte Felder** (Vorname/Nachname). Kiosk bekommt 2 Felder. |
| 2 | Info-Inhalte | Neues Modell **`InfoCategory`**; Alt-`StaticPage`-Inhalte **migrieren** (HTML→Markdown), StaticPage danach stillgelegt (bleibt als Tabelle, wird nicht mehr genutzt). |
| 3 | Admin-Login | **Benutzername + Passwort** (Flask-Login, mehrere Admins möglich). |
| 4 | PDF-Export | Server-seitig via **reportlab**, „schöner" Report (Kopf mit Logo/Zeitraum, Tabelle). |
| 5 | Logo/Branding | Datei-Upload nach **`instance/uploads/`** (überlebt Updates), Pfad in DB. |
| 6 | Kiosk-Props | Backdrop / Kfz-Feld / Auto-Rücksprung werden **echte Einstellungen**. |
| 7 | Frontend-Build | **Kein Build-Schritt**: Preact + htm über native ES-Module, Bibliotheken vendored. Grund: kein Node in Ziel-/Dev-Umgebung, simpler Apache+mod_wsgi-Deploy. |

## 1. Ziel-Architektur

```
gatekeeper/
  app/
    __init__.py         App-Factory: DB-Init, Migrationen, Seeds, SPA-Serving, API-Registrierung
    extensions.py       db, migrate, login_manager, csrf  (babel entfällt – SPA hält i18n)
    models.py           + correct_answer, AppSettings, AuditLog, InfoCategory
    mail.py             unverändert genutzt (Notfall + Monatsreport)
    audit.py            Helper log_audit(action, detail, user, ip)
    content_io.py       Export/Import der redaktionellen Inhalte (JSON)
    pdf.py              PDF-Report (reportlab)
    qr.py               QR-Code (SVG) für Check-out-Deeplink
    api/
      __init__.py       Blueprint-Registrierung /api
      public.py         /api/bootstrap, /api/checkin, /api/checkout
      admin.py          /api/admin/*  (login, visitors, stats, audit, info, health, settings, export/import, emergency)
    static/spa/
      index.html        SPA-Shell (von Flask für alle Nicht-/api-Pfade ausgeliefert)
      vendor/           preact.mjs, hooks.mjs, htm.mjs, qrcode.mjs  (vendored, kein CDN zur Laufzeit)
      styles.css        Design-Tokens + Komponenten-CSS (aus Prototyp-Inline-Styles überführt)
      src/
        main.mjs        Entry, globaler App-State, Routing kiosk/admin
        api.mjs         fetch-Wrapper inkl. CSRF-Header
        i18n.mjs        I18N (DE/EN/FR/ES) aus Prototyp
        theme.mjs       PALETTES + applyAccent
        wakeLock.mjs    iPad wach halten (+ Video-Fallback)
        markdown.mjs    blocksOf() (## Überschrift + Absätze)
        ui.mjs          Icon, Modal, Toast, StepDots, Field
        kiosk/          welcome, data, health, consent, sign, done, checkout, info
        admin/          login, shell, live, history, stats, audit, info, health, settings
  config.py             + UPLOAD_FOLDER, MAX_CONTENT_LENGTH
  requirements.txt      + reportlab, qrcode
  deploy/setup.sh       angepasst (uploads-Verzeichnis, keine Node-Abhängigkeit)
```

**Auth/CSRF:** Same-Origin (Flask liefert SPA + API). Flask-Login-Session-Cookie (`SameSite=Lax`, `HttpOnly`). Admin-Mutationen erfordern `X-CSRFToken`-Header (Token via `GET /api/csrf`). Öffentliche Kiosk-POSTs (checkin/checkout) sind CSRF-exempt (bewusst, da unauth. Kiosk-Aktion), aber rate-limitiert.

## 2. Datenmodell-Änderungen

### 2.1 `HealthQuestion` (erweitern)
- **+ `correct_answer` BOOLEAN NOT NULL DEFAULT 0** — Sollantwort (0 = „Nein" ist korrekt). Migration setzt bestehende Fragen auf `0` → **verhaltensgleich** zum Alt-System („jedes Ja blockt").
- Fragebogen-**Einleitungstext** je Sprache → in `AppSettings` (`health_intro_de/en/fr/es`).

### 2.2 `AppSettings` (neu, Single-Row id=1)
`company_name, logo_path(nullable), accent('blau'), retention_days(90), kiosk_backdrop('hell'), collect_plate(True), auto_return_seconds(20), health_intro_de/en/fr/es, updated_at`.

### 2.3 `AuditLog` (neu)
`id, created_at(UTC), action(code), detail(nullable), user(nullable), ip(nullable)`.
Aktionscodes: `login, checkout_admin, delete, export_csv, export_pdf, emergency, settings_saved, info_saved, health_saved, content_import`.

### 2.4 `InfoCategory` (neu, ersetzt `StaticPage` funktional)
`id, key(unique), type('dir'|'art'), icon, accent(hex), position, title_de/en/fr/es, body_de/en/fr/es(Markdown, für art), entries_json(JSON-Liste [{label:{de,en,fr,es}, value}] für dir), active, updated_at`.
7 Kategorien: `notruf(dir), kontakte(dir), notfall(art), hygiene(art), sicherheit(art), besucher(art), datenschutz(art)`.

### 2.5 `Visitor` — unverändert
first/last_name bleiben. Kein Schema-Change.

### 2.6 Migration & Seed (idempotent, in `__init__.py`)
- `ALTER TABLE health_questions ADD COLUMN correct_answer` (falls fehlt).
- `db.create_all()` legt `app_settings`, `audit_log`, `info_categories` an.
- Seed `AppSettings` id=1 (Defaults inkl. Health-Intro aus Prototyp).
- Seed `InfoCategory` (7 Kategorien mit Prototyp-Default-Inhalten, 4 Sprachen) falls leer.
- **Content-Migration:** bestehende `StaticPage`-Inhalte (admin-editiert, ≠ Platzhalter) per `_html_to_markdown()` in die passende `art`-Kategorie übernehmen (Slug→Key-Mapping). `dir`-Kategorien (notruf/kontakte) aus Prototyp-Defaults, da Alt-Inhalte nur Platzhalter.

## 3. API-Endpunkte

### Öffentlich
- `GET /api/bootstrap` → Branding, Kiosk-Config, Health-Intro+Fragen, Info-Kategorien (alle Sprachen).
- `POST /api/checkin` → validiert Antworten gg. `correct_answer`; bei Abweichung `422 blocked`. Erzeugt PIN, gibt `{pin, qr_svg}` (Deeplink `/?co=<pin>`).
- `POST /api/checkout` → `{pin}` (rate-limit 10/120s/IP) → `{duration}` oder `404`.
- `GET /api/csrf` → CSRF-Token.

### Admin (Login nötig)
- `POST /api/admin/login`, `POST /api/admin/logout`, `GET /api/admin/session`
- `GET /api/admin/visitors?scope=live|history&from&to&q`, `POST .../visitors/<id>/checkout`, `DELETE .../visitors/<id>`
- `GET /api/admin/export/csv`, `GET /api/admin/export/pdf`
- `GET /api/admin/stats`
- `GET /api/admin/audit`
- `GET /api/admin/info`, `PUT /api/admin/info/<key>`
- `GET /api/admin/health`, `PUT /api/admin/health`
- `GET /api/admin/settings`, `PUT /api/admin/settings`, `POST /api/admin/settings/logo`, `DELETE /api/admin/settings/logo`
- `POST /api/admin/emergency`, `POST /api/admin/smtp/test`
- `GET /api/admin/content/export` (JSON-Dump: Info + Health + Branding; **ohne** Besucherdaten & SMTP-Passwort)
- `POST /api/admin/content/import?mode=replace|fill&preview=0|1`

**SMTP-Passwort:** wird nie zurückgegeben (nur Feld „gesetzt: ja/nein"); Schreiben nur wenn Feld befüllt.

## 4. Frontend (Preact + htm, kein Build)

- Globaler State via `useReducer` in `main.mjs` (entspricht Prototyp-`state`), Screens als Komponenten.
- **i18n** komplett aus Prototyp (`I18N`), statische UI-Texte; dynamische Inhalte (Fragen, Info, Branding) vom Server.
- **Theming** über CSS-Variablen (`--accent`, `--accent-dark`, `--accent-soft`), 5 Presets.
- **QR** vom Server (SVG) → einfach als Bild anzeigen (kein JS-QR-Lib nötig; `qrcode.mjs`-Vendor nur falls clientseitig gewünscht — Default: Server).
- **Wake Lock** (`navigator.wakeLock`) mit Re-Acquire bei `visibilitychange` + stummer-Video-Fallback für ältere iPadOS.
- **Signatur**: Canvas → PNG-DataURL (wie Prototyp), an `/api/checkin`.
- Kiosk-Flow: `welcome → data → health → consent → sign → done`; Checkout: `cocode → codone`; Info-Hub.
- Admin: Login → Shell (KPIs, Tabs) → live/history/stats/audit/info/health/settings.

## 5. Export/Import (User-Wunsch)

- **Export** `GET /api/admin/content/export` → `gatekeeper-content-YYYYMMDD.json`
  ```json
  { "schema": 1, "exported_at": "...", "info": [...], "health": {"intro":{...},"questions":[...]}, "branding": {"company_name":..,"accent":..} }
  ```
  Kein Besucherdatensatz, kein SMTP-Passwort, Logo optional als Base64.
- **Import** `POST /api/admin/content/import` — Datei-Upload, `preview=1` liefert Diff-Zusammenfassung, dann `mode=replace` (überschreiben) oder `mode=fill` (nur leere Felder). Schema-Version-Check. Audit `content_import`.

## 6. Umsetzungsreihenfolge (Phasen)

1. **Backend-Fundament:** models.py (neue Modelle), extensions.py, config.py, __init__.py (Seeds/Migration/SPA-Serving).
2. **API:** api/public.py, api/admin.py, audit.py, pdf.py, qr.py, content_io.py.
3. **Frontend-Gerüst:** index.html, vendor/, styles.css, main.mjs, api.mjs, i18n.mjs, theme.mjs, ui.mjs, wakeLock.mjs, markdown.mjs.
4. **Kiosk-Screens.**
5. **Admin-Tabs.**
6. **Deploy/Doku:** requirements.txt, deploy/setup.sh, CLAUDE.md aktualisieren.
7. **Abschluss-Review** (da kein lokaler Python/Node-Lauf möglich: sorgfältige statische Prüfung; Funktionstest auf VM dev-1).

## 7. Hinweise / Risiken

- **Kein lokaler Lauf** (kein Python/Node auf dev-Windows) → Verifikation statisch; End-to-End-Test auf der VM.
- **Wake Lock braucht HTTPS** → über den Reverse-Proxy des Users bereitzustellen.
- **Kein Datenverlust:** StaticPage-Tabelle bleibt erhalten; Migration nur additiv.
- **Google Fonts** per `<link>` (wie Prototyp) mit System-Font-Fallback; optionales Vendoring als Härtung später.
