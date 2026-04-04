"""Flask application factory for GateKeeper."""

import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import click
from flask import Flask, request, session

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
        config_name = os.environ.get("GATEKEEPER_ENV", os.environ.get("FLASK_ENV", "development"))

    app = Flask(__name__)
    config_cls = config_map[config_name]
    app.config.from_object(config_cls)

    # Call init_app hook if config class provides one (e.g. production safety checks)
    if hasattr(config_cls, "init_app"):
        config_cls.init_app(app)

    # Initialize extensions
    from app.extensions import db, migrate, login_manager, babel, csrf

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Babel locale selector
    def get_locale():
        lang = session.get("lang")
        if lang and lang in app.config["LANGUAGES"]:
            return lang
        return request.accept_languages.best_match(
            app.config["LANGUAGES"], "de"
        )

    babel.init_app(app, locale_selector=get_locale)

    # Jinja2 filter for timezone conversion
    app.jinja_env.filters["to_berlin"] = to_berlin

    # Make get_locale and current year available in templates
    @app.context_processor
    def inject_globals():
        return {"get_locale": get_locale, "current_year": datetime.now(timezone.utc).year}

    @app.context_processor
    def inject_now():
        return {"now": datetime.now}

    # Register blueprints
    from app.visitor import visitor_bp
    from app.admin import admin_bp

    app.register_blueprint(visitor_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # CLI commands
    register_cli(app)

    # Create tables and seed data on first request (dev convenience)
    with app.app_context():
        from app.models import AdminUser, HealthQuestion, SmtpSettings, StaticPage

        db.create_all()
        _seed_defaults(db, AdminUser, StaticPage, SmtpSettings, HealthQuestion, app)

    return app


_HYGIENE_DE = """\
<p>Sollten Sie eine oder mehr Fragen bejaht haben, dürfen Sie den Produktionsbereich
nur in Begleitung bzw. nach Rücksprachen mit der besuchten Person betreten.</p>
<p>Unabhängig davon bitten wir Sie folgende Hygieneregeln zu befolgen:</p>
<ol>
<li>Für die Dauer Ihres Aufenthaltes in den Produktionsräumen ist der zur Verfügung
gestellte Kittel zu tragen.</li>
<li>Bitte waschen und desinfizieren Sie sich vor Betreten der Produktionsräume die
Hände und legen Sie die vorgesehene Kopfbedeckung (Haarnetz) an.</li>
<li>Bitte legen Sie Uhren und jeglichen Schmuck ab.</li>
<li>Bitte rauchen Sie nur in den dafür gekennzeichneten Bereichen.</li>
<li>Bitte essen, bzw. trinken Sie nicht in den Produktionsräumen (einschließlich Kaugummi).</li>
<li>Bitte tragen Sie keinen Nagellack, bzw. Kunstnägel.</li>
<li>Schnittverletzungen bitte mit einem Spezial-Pflaster versorgen
(bei Bedarf bitte an der Rezeption fragen).</li>
</ol>
"""

_HYGIENE_EN = """\
<p>If visitor/contractor answers yes to any of the questionnaire above, entry to
production may not be permitted – contact technical department for guidance.</p>
<p>Entry to production areas is subject to the visitor/contractor complying
with the following hygiene rules:</p>
<ol>
<li>Company issued coat must be worn.</li>
<li>Use antibacterial hand cleanser and hand wash basin and wear a hairnet.</li>
<li>Remove all jewellery and watches except plain rings.</li>
<li>No smoking except in designated areas.</li>
<li>No drinking or eating (including chewing gum).</li>
<li>No nail varnish or false nails.</li>
<li>All cuts to be covered with a suitable plaster.</li>
</ol>
"""

_SAFETY_DE = """\
<p>Sehr geehrte Damen und Herren,<br>
wir heißen Sie in unserem Unternehmen herzlich willkommen.
Im Sinne der Werksicherheit, Hygiene und Umweltschutz müssen wir Sie bitten, dass Sie
während ihres Aufenthaltes folgende Punkte streng beachten:</p>
<h3>Rauchen</h3>
<p>Auf dem gesamten Werksgelände gilt ein absolutes Rauchverbot (auch E-Zigaretten).
Rauchen ist nur in den ausgewiesenen Raucherzonen erlaubt (siehe Hinweisschilder).</p>
<h3>Handys</h3>
<p>Handys dürfen nur auf dem Freigelände, in Büro- und Verwaltungsgebäuden eingeschaltet
sein. Handys, in denen eine Kamera integriert ist (Fotohandys) sind im Werk untersagt.</p>
<h3>Fotografieren</h3>
<p>Das Fotografieren innerhalb der Betriebsgebäude ist nur nach Genehmigung durch
die Begleitperson / den Abteilungsleiter zulässig.</p>
<h3>Schmuck</h3>
<p>Das Tragen von Uhren, Halsketten, Ohrringen, Armbändern ist im gesamten
Produktionsbereich nicht gestattet.</p>
<h3>Produktionsräume</h3>
<p>In unseren Produktionsräumen darf weder gegessen noch getrunken werden. Türen
und Tore sind stets geschlossen zu halten. Sie dürfen nur auf direktem Weg zu Ihrer
Arbeitsstelle / zum vereinbarten Einsatzort in der Produktion gehen. Im gesamten
Produktionsbereich (Hygienezone) ist das Tragen einer Kopfbedeckung (Haarnetz)
vorgeschrieben. Haarnetzspender finden Sie an den jeweiligen Eingängen.</p>
<h3>Arbeitsmittel</h3>
<p>Ohne Genehmigung der Projektverantwortlichen dürfen keine
Arbeitsmittel wie Fette, Farben, Grundiermittel, Lösungsmittel, Reinigungsmittel,
sowie Chemikalien aller Art verwendet werden.<br>
Nur einwandfreie elektrische Betriebsmittel / Werkzeuge, die mit einer gültigen
Prüfplakette nach BGV A3 versehen sind, dürfen an dem 230 / 400V Werksnetz
betrieben werden.</p>
<h3>LKW / PKW Verkehr</h3>
<p>LKW dürfen nur an den zugewiesenen Stellen geparkt werden. PKW sind auf dem
Parkplatz vor der Druckerei abzustellen.<br>
Die Geschwindigkeit auf dem Werksgelände beträgt 10 km/h und es gilt die allgemeine
Straßenverkehrsordnung.</p>
<h3>Datensicherheit</h3>
<p>Die Verwendung von Datenträgern z.B. Memory Sticks, CD / DVD, etc., ist nur nach
Freigabe durch die Fachabteilung erlaubt. Programmiergeräte sowie Laptops dürfen
nur mit einem aktuellen Anti-Virus-Programm nach Rücksprache mit der Fachabteilung
im Produktions-Netzwerk betrieben werden.</p>
<h3>Arbeitsschutz / Hygiene / Umweltschutz</h3>
<p>Alle gültigen Vorschriften bezüglich Arbeitssicherheit, Hygiene und Umweltschutz sind
unbedingt einzuhalten (inkl. Arbeits- / Besucherkleidung; Wundversorgung).</p>
<h3>Feuerarbeiten</h3>
<p>Feuerarbeiten wie Schweißen, Löten, Schleifen außerhalb des Werkstattbereiches
und Dachdeckerarbeiten, die den Umgang mit offener Flamme erforderlich machen,
dürfen nur mit einer Genehmigung von dem Projektleiter / Auftraggeber durchgeführt
werden.</p>
<h3>Feueralarm</h3>
<p>Bei Feueralarm die Gebäude sofort verlassen. Die Alarmierung erfolgt durch eine Sirene.
Entsprechende Sammelstellen aufsuchen (siehe ausgehängte Flucht- u. Rettungspläne).</p>
<h3>Krankheiten</h3>
<p>Besucher mit meldepflichtigen Krankheiten gem. Infektionsschutzgesetz (IfSG) §42
dürfen das Produktionsgebäude nicht betreten. Melden Sie sich bei der zu besuchenden
Person, wenn Sie an einer der nachfolgend aufgeführten Krankheiten leiden oder
wenn der Verdacht auf eine dieser Erkrankungen besteht:<br>
Typhus oder Paratyphus, Virushepatitis A oder E, Cholera, Shigellenruhr, Salmonellose,
andere infektiöse Gastroenteritis, infektiöse Wunden oder ansteckende Hautkrankheiten.</p>
<p><strong>Vielen Dank – Die Betriebsleitung (General Manager)</strong></p>
"""

_SAFETY_EN = """\
<p>Dear Sir / Madam,<br>
We welcome you to our company.
For the purpose of industrial safety, hygiene and environmental protection, we kindly ask
you to strictly observe the following during your visit:</p>
<h3>Smoking</h3>
<p>Smoking is strictly banned on the entire factory premises (including e-cigarettes).
Smoking is only permitted in designated smoking areas (see information signs).</p>
<h3>Mobile phones</h3>
<p>Mobile phones may only be switched on outside and in the office and administrative
buildings. Mobile phones with an integrated camera (camera mobile phones) are not
permitted in the factory.</p>
<h3>Taking photographs</h3>
<p>Photos may only be taken inside the company premises with the approval of the
escort / department head.</p>
<h3>Jewellery</h3>
<p>No watches, necklaces, earrings or bracelets may be worn anywhere in the
production area.</p>
<h3>Production areas</h3>
<p>Eating and drinking are forbidden in our production areas. Doors and gates are to be
kept closed at all times. You must go direct to your workplace / to the agreed operating
location in production. The entire production area (hygiene zone) wearing a head
covering (hairnet) is prescribed. Hairnet dispensers are found at the respective entrance doors.</p>
<h3>Work equipment</h3>
<p>No work equipment such as grease, paint, primer, solvents, cleaning agents and
chemicals of any kind may be used without the prior approval of those responsible for
the project management.<br>
Only electrical operating material / tools that are in a perfect condition and bear a valid
BGV A3 test label may be operated in the 230 / 400V factory network.</p>
<h3>Car / lorry traffic</h3>
<p>Lorries may only be parked in the designated parking spaces. Cars are to be parked
on the parking place in front of the printing plant.<br>
Vehicles are to be driven at 10 km/h on the factory premises. General traffic regulations
valid in Germany apply.</p>
<h3>Data security</h3>
<p>Data media, e.g., memory sticks, CDs / DVDs, etc., may only be used with the prior
approval of the specialist department. Programmers and laptops may only be used in
the production network after consulting the specialist department and provided that an
up-to-date anti-virus program has been installed.</p>
<h3>Occupational safety / hygiene / environmental protection</h3>
<p>It is absolutely essential that valid regulations concerning occupational safety, hygiene
and environmental protection are complied with (incl. workwear / visitors' clothing;
the care of wounds).</p>
<h3>Working with fire</h3>
<p>Work that involves working with fire such as welding, soldering and grinding outside
the factory area and roofing work which requires the handling of open flames may only
be carried out with the prior approval of the project manager / client.</p>
<h3>Fire alarm</h3>
<p>Leave the building immediately if the fire alarm goes off. The alarm warns with a siren.
Go to the relevant collection points (see attached emergency exits and evacuation plans).</p>
<h3>Illness</h3>
<p>Visitors with a reportable illness under § 42 of the German Infection Protection Law
(IfSG) may not enter the production building. Report to the person to be visited if you
suffer from one of the following illnesses or if there is any suspicion of one of these
illnesses: Typhus or paratyphoid fever, viral hepatitis A or E, cholera, shigella
dysentery, salmonellosis, other infectious gastroenteritis, infectious wounds or
infectious skin diseases.</p>
<p><strong>Many thanks – The Plant Manager (General Manager)</strong></p>
"""


def _seed_defaults(db, AdminUser, StaticPage, SmtpSettings, HealthQuestion, app):
    """Seed default admin user, static pages, and health questions if not present."""
    if not AdminUser.query.first():
        admin = AdminUser(username="admin")
        admin.set_password(app.config.get("ADMIN_DEFAULT_PASSWORD", "admin"))
        db.session.add(admin)

    default_pages = [
        ("emergency_contacts", "Kontakte", "Contacts",
         "<p>Inhalt wird noch eingepflegt.</p>", "<p>Content will be added soon.</p>"),
        ("emergency_plans", "Notfallpläne", "Emergency Plans",
         "<p>Inhalt wird noch eingepflegt.</p>", "<p>Content will be added soon.</p>"),
        ("emergency_numbers", "Notrufnummern", "Emergency Numbers",
         "<p>Inhalt wird noch eingepflegt.</p>", "<p>Content will be added soon.</p>"),
        ("visitor_info", "Besucherinformationen", "Visitor Information",
         "<p>Inhalt wird noch eingepflegt.</p>", "<p>Content will be added soon.</p>"),
        ("hygiene_rules", "Hygieneregeln", "Hygiene Rules",
         _HYGIENE_DE, _HYGIENE_EN),
        ("safety_conduct", "Sicherheits-/Verhaltenshinweise", "Rules of safety / conduct",
         _SAFETY_DE, _SAFETY_EN),
    ]
    for slug, title_de, title_en, content_de, content_en in default_pages:
        if not StaticPage.query.filter_by(slug=slug).first():
            db.session.add(
                StaticPage(
                    slug=slug,
                    title_de=title_de,
                    title_en=title_en,
                    content_de=content_de,
                    content_en=content_en,
                )
            )
    # Seed default empty SMTP settings row (id=1)
    if not db.session.get(SmtpSettings, 1):
        db.session.add(SmtpSettings(id=1, smtp_port=587, use_tls=True, enabled=False))

    # Seed default health questions (if table is empty)
    if not HealthQuestion.query.first():
        default_questions = [
            (1, "flu", "Erkältungskrankheiten (Husten, Schnupfen, Fieber)",
             "Flu diseases (cough, runny nose, fever)"),
            (2, "diarrhea", "Durchfall oder Erbrechen",
             "Diarrhoea or vomiting"),
            (3, "food_poisoning",
             "Salmonellen-, Campylobacter-, Shigellen- oder E. Coli-Lebensmittelvergiftung",
             "Salmonella, Campylobacter, Shigella or E. Coli food poisoning"),
            (4, "parasites", "Parasitäre Infektionen",
             "Any parasitic infection"),
            (5, "ent", "Hals-Nasen-Ohren-Infektionen",
             "Ear, nose or throat infections"),
            (6, "skin", "Hauterkrankungen oder offene, eitrige Wunden",
             "Skin rashes or open, festering wounds"),
        ]
        for pos, key, text_de, text_en in default_questions:
            db.session.add(HealthQuestion(
                position=pos, short_key=key, text_de=text_de, text_en=text_en, active=True
            ))

    db.session.commit()


def register_cli(app: Flask):
    """Register custom Flask CLI commands."""

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
    @click.option("--days", default=90, help="Delete records older than N days")
    def cleanup_visitors(days):
        """Delete visitor records older than N days (DSGVO compliance)."""
        from app.extensions import db
        from app.models import Visitor

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        count = Visitor.query.filter(Visitor.created_at < cutoff).delete()
        db.session.commit()
        click.echo(f"Deleted {count} visitor records older than {days} days.")
