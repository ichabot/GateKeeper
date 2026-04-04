"""Email helper for GateKeeper – monthly visitor report via SMTP."""

import csv
import io
import smtplib
from calendar import monthrange
from datetime import datetime, time, timezone
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app import BERLIN_TZ, to_berlin


def _fmt_berlin(dt):
    """Format a datetime in Berlin timezone as dd.mm.yyyy HH:MM."""
    if dt is None:
        return "—"
    return to_berlin(dt).strftime("%d.%m.%Y %H:%M")


def get_previous_month(now=None):
    """Return (year, month) for the previous month. Handles Jan->Dec rollover."""
    if now is None:
        now = datetime.now(timezone.utc)
    if now.month == 1:
        return now.year - 1, 12
    return now.year, now.month - 1


def _smtp_connect(settings):
    """Create and authenticate an SMTP connection."""
    if settings.use_tls:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
    else:
        server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30)
    server.login(settings.smtp_user, settings.smtp_password)
    return server

_MONTH_NAMES_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


def send_emergency_report(settings) -> tuple[bool, str | None]:
    """Send emergency evacuation list with ALL visitors still on-site.

    Returns (True, None) on success or (False, error_message) on failure.
    """
    from app.models import Visitor  # lazy import avoids circular dependency

    now_berlin = to_berlin(datetime.now(timezone.utc))

    on_site = (
        Visitor.query.filter(
            Visitor.departure_time.is_(None),
        )
        .order_by(Visitor.arrival_time.asc())
        .all()
    )

    timestamp = now_berlin.strftime("%d.%m.%Y %H:%M")

    subject = f"NOTFALL – Aktuelle Besucherliste ({len(on_site)} Person(en) im Gebäude) – {timestamp} Uhr"

    lines = [
        "NOTFALL-EVAKUIERUNGSLISTE",
        f"Erstellt: {timestamp} Uhr",
        "",
        f"Aktuell im Gebäude befindliche Besucher: {len(on_site)}",
        "",
    ]
    if on_site:
        lines.append("NAME                    FIRMA                   ANSPRECHPARTNER         KFZ          ANKUNFT")
        lines.append("-" * 95)
        for v in on_site:
            arrival = _fmt_berlin(v.arrival_time)
            plate = v.license_plate or "—"
            lines.append(
                f"{(v.first_name + ' ' + v.last_name):<24}"
                f"{v.company:<24}"
                f"{v.contact_person:<24}"
                f"{plate:<13}"
                f"{arrival}"
            )
    else:
        lines.append("Keine Besucher aktuell im Gebäude.")

    lines += [
        "",
        "-- GateKeeper Besuchermanagement",
        "Bitte sicherstellen, dass alle oben genannten Personen evakuiert wurden.",
    ]

    body = "\n".join(lines)

    msg = MIMEMultipart()
    msg["From"] = settings.smtp_sender
    recipients = [r.strip() for r in settings.emergency_recipients.split(",") if r.strip()]
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    server = None
    try:
        server = _smtp_connect(settings)
        server.send_message(msg)
        return True, None
    except Exception as exc:
        return False, str(exc)
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass


def build_monthly_csv(year: int, month: int) -> tuple[str, int]:
    """Return (csv_string, visitor_count) for the given year/month."""
    from app.models import HealthQuestion, Visitor  # lazy import avoids circular dependency

    # Calculate month boundaries in Berlin timezone, then convert to UTC for DB query
    last_day = monthrange(year, month)[1]
    berlin_start = datetime(year, month, 1, 0, 0, 0, tzinfo=BERLIN_TZ)
    berlin_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=BERLIN_TZ)
    start = berlin_start.astimezone(timezone.utc)
    end = berlin_end.astimezone(timezone.utc)

    visitors = (
        Visitor.query.filter(
            Visitor.arrival_time >= start,
            Visitor.arrival_time <= end,
        )
        .order_by(Visitor.arrival_time.asc())
        .all()
    )

    # Dynamic health question columns
    questions = HealthQuestion.query.order_by(HealthQuestion.position).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    header = [
        "Vorname", "Nachname", "Firma", "Ansprechpartner", "KFZ-Kennzeichen",
        "Ankunft", "Abfahrt", "Status",
    ]
    for q in questions:
        header.append(q.text_de[:50])
    writer.writerow(header)

    for v in visitors:
        row = [
            v.first_name, v.last_name, v.company, v.contact_person,
            v.license_plate or "",
            _fmt_berlin(v.arrival_time) if v.arrival_time else "",
            _fmt_berlin(v.departure_time) if v.departure_time else "",
            "Vor Ort" if v.is_on_site else "Abgereist",
        ]
        answers = v.get_answers_for_csv()
        for q in questions:
            row.append(answers.get(q.short_key, ""))
        writer.writerow(row)

    return output.getvalue(), len(visitors)


def send_monthly_report(settings, year: int, month: int) -> tuple[bool, str | None]:
    """Send monthly visitor CSV report via SMTP.

    Returns (True, None) on success or (False, error_message) on failure.
    """
    csv_content, count = build_monthly_csv(year, month)
    month_name = _MONTH_NAMES_DE[month - 1]
    csv_filename = f"besucher_{year}_{month:02d}.csv"

    subject = f"GateKeeper – Besucherbericht {month_name} {year} ({count} Einträge)"
    body = (
        f"Guten Tag,\n\n"
        f"anbei der Besucherbericht für {month_name} {year}.\n"
        f"Gesamtzahl der Einträge: {count}\n\n"
        f"Die Datei kann in Excel geöffnet werden (Trennzeichen: Semikolon).\n\n"
        f"-- GateKeeper Besuchermanagement"
    )

    msg = MIMEMultipart()
    msg["From"] = settings.smtp_sender
    recipients = [r.strip() for r in settings.smtp_recipients.split(",") if r.strip()]
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # UTF-8 BOM prefix so Excel opens the CSV without encoding issues
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(("\ufeff" + csv_content).encode("utf-8"))
    encoders.encode_base64(attachment)
    attachment.add_header(
        "Content-Disposition", f'attachment; filename="{csv_filename}"'
    )
    msg.attach(attachment)

    server = None
    try:
        server = _smtp_connect(settings)
        server.send_message(msg)
        return True, None
    except Exception as exc:
        return False, str(exc)
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass
