"""Flask application factory for GateKeeper (React-SPA + JSON-API redesign)."""

import mimetypes
import os
import re
from datetime import datetime, time, timedelta, timezone
from html import unescape
from zoneinfo import ZoneInfo

import click
from flask import Flask, abort, jsonify, send_from_directory

# ES modules must be served with a JavaScript MIME type or the browser refuses
# to execute them. Register it so Flask's static handler (behind gunicorn)
# serves .mjs correctly.
mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("font/woff2", ".woff2")

# Berlin timezone for display conversions
BERLIN_TZ = ZoneInfo("Europe/Berlin")


def to_berlin(dt):
    """Convert a UTC datetime to Europe/Berlin for display."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(BERLIN_TZ)


from config import config_map


def create_app(config_name: str | None = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get(
            "GATEKEEPER_ENV", os.environ.get("FLASK_ENV", "development")
        )

    app = Flask(__name__, static_folder="static", static_url_path="/static")
    config_cls = config_map[config_name]
    app.config.from_object(config_cls)

    if hasattr(config_cls, "init_app"):
        config_cls.init_app(app)

    # --- Instance & uploads directories -----------------------------------
    os.makedirs(app.instance_path, exist_ok=True)
    upload = app.config.get("UPLOAD_FOLDER", "uploads")
    if not os.path.isabs(upload):
        upload = os.path.join(app.instance_path, upload)
    app.config["UPLOAD_FOLDER"] = upload
    os.makedirs(upload, exist_ok=True)

    # --- Extensions --------------------------------------------------------
    from app.extensions import db, login_manager, csrf

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.unauthorized_handler
    def _unauthorized():
        return jsonify({"error": "unauthorized"}), 401

    # --- JSON API ----------------------------------------------------------
    from app.api import register_api

    register_api(app, csrf)

    # --- SPA + uploads serving --------------------------------------------
    _register_spa(app)

    # --- CLI ---------------------------------------------------------------
    register_cli(app)

    # --- DB bootstrap: create tables, migrate, seed ------------------------
    with app.app_context():
        from app import models  # noqa: F401  (register models with SQLAlchemy)

        db.create_all()
        _run_migrations(db)
        _seed_defaults(db, app)

    return app


# ---------------------------------------------------------------------------
# SPA serving
# ---------------------------------------------------------------------------
def _register_spa(app: Flask):
    spa_dir = os.path.join(app.static_folder, "spa")

    @app.route("/")
    def _spa_index():
        return send_from_directory(spa_dir, "index.html")

    @app.route("/uploads/<path:filename>")
    def _uploads(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/<path:path>")
    def _spa_catchall(path):
        # Never hijack API/static/uploads (they have their own, more specific rules).
        if path.startswith(("api/", "static/", "uploads/")):
            abort(404)
        full = os.path.join(spa_dir, path)
        if os.path.isfile(full):
            return send_from_directory(spa_dir, path)
        # Unknown path -> SPA shell (client decides what to render).
        return send_from_directory(spa_dir, "index.html")


# ---------------------------------------------------------------------------
# Migrations (idempotent, plain SQLite ALTERs for existing installs)
# ---------------------------------------------------------------------------
def _run_migrations(db):
    conn = db.engine.raw_connection()
    cur = conn.cursor()

    def has_col(table, col):
        cur.execute(f"PRAGMA table_info({table})")
        return any(row[1] == col for row in cur.fetchall())

    def table_exists(table):
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        )
        return cur.fetchone() is not None

    stmts = []
    if table_exists("health_questions"):
        if not has_col("health_questions", "text_fr"):
            stmts.append("ALTER TABLE health_questions ADD COLUMN text_fr TEXT NOT NULL DEFAULT ''")
        if not has_col("health_questions", "text_es"):
            stmts.append("ALTER TABLE health_questions ADD COLUMN text_es TEXT NOT NULL DEFAULT ''")
        if not has_col("health_questions", "correct_answer"):
            stmts.append("ALTER TABLE health_questions ADD COLUMN correct_answer BOOLEAN NOT NULL DEFAULT 0")
    if table_exists("static_pages"):
        for col in ("title_fr", "title_es", "content_fr", "content_es"):
            if not has_col("static_pages", col):
                ctype = "VARCHAR(200)" if col.startswith("title") else "TEXT"
                stmts.append(
                    f"ALTER TABLE static_pages ADD COLUMN {col} {ctype} NOT NULL DEFAULT ''"
                )
    if table_exists("visitors"):
        if not has_col("visitors", "profile_token"):
            stmts.append("ALTER TABLE visitors ADD COLUMN profile_token VARCHAR(24)")
        if not has_col("visitors", "auto_checked_out"):
            stmts.append("ALTER TABLE visitors ADD COLUMN auto_checked_out BOOLEAN NOT NULL DEFAULT 0")

    for stmt in stmts:
        cur.execute(stmt)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# HTML -> Markdown (best-effort, for migrating old StaticPage content)
# ---------------------------------------------------------------------------
_PLACEHOLDER_MARKERS = (
    "wird noch eingepflegt",
    "will be added soon",
    "sera ajouté prochainement",
    "se añadirá próximamente",
)


def _html_to_markdown(html: str) -> str:
    if not html:
        return ""
    if any(m in html for m in _PLACEHOLDER_MARKERS):
        return ""  # treat placeholder as "no content"
    text = html
    # headings -> "## "
    text = re.sub(r"<h[1-6][^>]*>", "\n## ", text, flags=re.I)
    text = re.sub(r"</h[1-6]>", "\n", text, flags=re.I)
    # list items -> line each
    text = re.sub(r"<li[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"</li>", "", text, flags=re.I)
    # paragraph / br / block breaks -> newline
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</p>|</div>", "\n", text, flags=re.I)
    # strip all remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    # collapse whitespace per line, drop empty lines
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------
def _seed_defaults(db, app):
    from app.models import (
        AdminUser, AppSettings, HealthQuestion, InfoCategory, SmtpSettings, StaticPage,
    )
    from app.seed_content import (
        DEFAULT_QUESTIONS, DEFAULT_SETTINGS, HEALTH_INTRO, HQ_FR_ES_BACKFILL,
        INFO_CATEGORIES, STATICPAGE_SLUG_TO_KEY,
    )

    # Admin user
    if not AdminUser.query.first():
        admin = AdminUser(username="admin")
        admin.set_password(app.config.get("ADMIN_DEFAULT_PASSWORD", "admin"))
        db.session.add(admin)

    # SMTP settings row (id=1)
    if not db.session.get(SmtpSettings, 1):
        db.session.add(SmtpSettings(id=1, smtp_port=587, use_tls=True, enabled=False))

    # Health questions
    if not HealthQuestion.query.first():
        for pos, key, de, en, fr, es in DEFAULT_QUESTIONS:
            db.session.add(HealthQuestion(
                position=pos, short_key=key,
                text_de=de, text_en=en, text_fr=fr, text_es=es,
                active=True, correct_answer=False,
            ))

    # App settings (id=1) incl. questionnaire intro
    if not db.session.get(AppSettings, 1):
        db.session.add(AppSettings(
            id=1,
            company_name=DEFAULT_SETTINGS["company_name"],
            accent=DEFAULT_SETTINGS["accent"],
            retention_days=DEFAULT_SETTINGS["retention_days"],
            kiosk_backdrop=DEFAULT_SETTINGS["kiosk_backdrop"],
            collect_plate=DEFAULT_SETTINGS["collect_plate"],
            auto_return_seconds=DEFAULT_SETTINGS["auto_return_seconds"],
            health_intro_de=HEALTH_INTRO["de"], health_intro_en=HEALTH_INTRO["en"],
            health_intro_fr=HEALTH_INTRO["fr"], health_intro_es=HEALTH_INTRO["es"],
        ))

    db.session.commit()

    # FR/ES backfill on existing health questions (older installs)
    for key, (tfr, tes) in HQ_FR_ES_BACKFILL.items():
        q = HealthQuestion.query.filter_by(short_key=key).first()
        if q and not q.text_fr:
            q.text_fr = tfr
            q.text_es = tes
    db.session.commit()

    # Info categories (first run only)
    if not InfoCategory.query.first():
        for c in INFO_CATEGORIES:
            cat = InfoCategory(
                key=c["key"], type=c["type"], icon=c["icon"], accent=c["accent"],
                position=c["position"], active=True,
                title_de=c["title"]["de"], title_en=c["title"]["en"],
                title_fr=c["title"]["fr"], title_es=c["title"]["es"],
            )
            if c["type"] == "art":
                b = c["body"]
                cat.body_de, cat.body_en = b["de"], b["en"]
                cat.body_fr, cat.body_es = b["fr"], b["es"]
            else:
                cat.entries = c.get("entries", [])
            db.session.add(cat)
        db.session.commit()

        # Migrate admin-edited StaticPage content into the matching art category
        _migrate_staticpages(db, StaticPage, InfoCategory, STATICPAGE_SLUG_TO_KEY)


def _migrate_staticpages(db, StaticPage, InfoCategory, slug_to_key):
    """Pull any non-placeholder StaticPage content into the corresponding
    InfoCategory (art types only), converting HTML to Markdown."""
    changed = False
    for slug, key in slug_to_key.items():
        page = StaticPage.query.filter_by(slug=slug).first()
        if not page:
            continue
        cat = InfoCategory.query.filter_by(key=key).first()
        if not cat or cat.type != "art":
            continue
        for lang in ("de", "en", "fr", "es"):
            md = _html_to_markdown(getattr(page, f"content_{lang}", "") or "")
            if md:
                setattr(cat, f"body_{lang}", md)
                changed = True
    if changed:
        db.session.commit()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def register_cli(app: Flask):
    """Register custom Flask CLI commands (used by cron on the server)."""

    @app.cli.command("seed-admin")
    @click.option("--username", default="admin", help="Admin username")
    @click.option("--password", prompt=True, hide_input=True, help="Admin password")
    def seed_admin(username, password):
        """Create or reset an admin user."""
        from app.extensions import db
        from app.models import AdminUser

        user = AdminUser.query.filter_by(username=username).first()
        if user:
            user.set_password(password)
            click.echo(f"Password updated for '{username}'.")
        else:
            user = AdminUser(username=username)
            user.set_password(password)
            db.session.add(user)
            click.echo(f"Admin user '{username}' created.")
        db.session.commit()

    @app.cli.command("send-monthly-report")
    def send_monthly_report_cmd():
        """Send previous month's visitor CSV report via SMTP (for cron use)."""
        from app.extensions import db
        from app.models import SmtpSettings
        from app.mail import get_previous_month, send_monthly_report

        settings = db.session.get(SmtpSettings, 1)
        if not settings:
            click.echo("ERROR: Keine SMTP-Einstellungen in der Datenbank gefunden.")
            return
        if not settings.enabled:
            click.echo("INFO: Monatlicher E-Mail-Versand ist deaktiviert (Admin > SMTP).")
            return
        if not settings.smtp_host or not settings.smtp_recipients:
            click.echo("ERROR: SMTP-Einstellungen unvollständig.")
            return

        year, month = get_previous_month()
        click.echo(f"Sende Besucherbericht {month:02d}/{year} ...")
        ok, err = send_monthly_report(settings, year, month)
        if ok:
            click.echo(f"Erfolgreich gesendet an: {settings.smtp_recipients}")
        else:
            click.echo(f"FEHLER: {err}")

    @app.cli.command("cleanup-visitors")
    @click.option("--days", default=None, type=int,
                  help="Delete records older than N days (default: AppSettings.retention_days)")
    def cleanup_visitors(days):
        """Delete visitor records older than N days (DSGVO compliance)."""
        from app.extensions import db
        from app.models import AppSettings, Visitor, VisitorProfile

        if days is None:
            settings = db.session.get(AppSettings, 1)
            days = settings.retention_days if settings else 90

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        count = Visitor.query.filter(Visitor.created_at < cutoff).delete()
        # Returning-visitor profiles expire on inactivity (last check-in).
        prof_count = VisitorProfile.query.filter(
            VisitorProfile.last_seen_at < cutoff
        ).delete()
        db.session.commit()
        click.echo(
            f"Deleted {count} visitor records and {prof_count} inactive "
            f"visitor profiles older than {days} days."
        )

    @app.cli.command("auto-checkout")
    def auto_checkout():
        """Auto-checkout visitors who forgot to check out (for nightly cron)."""
        from app.extensions import db
        from app.models import Visitor

        berlin_today = datetime.now(BERLIN_TZ).date()
        today_start_utc = datetime.combine(
            berlin_today, time(0, 0, 0), tzinfo=BERLIN_TZ
        ).astimezone(timezone.utc)
        missed = Visitor.query.filter(
            Visitor.departure_time.is_(None),
            Visitor.arrival_time < today_start_utc,
        ).all()
        for v in missed:
            arrival_berlin = (
                v.arrival_time.astimezone(BERLIN_TZ)
                if v.arrival_time.tzinfo else v.arrival_time
            )
            v.departure_time = datetime.combine(
                arrival_berlin.date(), time(23, 59, 59), tzinfo=BERLIN_TZ
            ).astimezone(timezone.utc)
            v.auto_checked_out = True
        db.session.commit()
        click.echo(f"Auto-checkout: {len(missed)} visitor(s) checked out.")
