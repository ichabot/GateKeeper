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

_MONTH_NAMES_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


def send_emergency_report(settings) -> tuple[bool, str | None]:
    """Send emergency evacuation list with visitors checked in today and still on-site.

    Returns (True, None) on success or (False, error_message) on failure.
    """
    from app.models import Visitor  # lazy import avoids circular dependency

    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min).replace(tzinfo=timezone.utc)

    on_site = (
        Visitor.query.filter(
            Visitor.departure_time.is_(None),
            Visitor.arrival_time >= today_start,
        )
        .order_by(Visitor.arrival_time.asc())
        .all()
    )

    timestamp = now.strftime("%d.%m.%Y %H:%M")

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
            arrival = v.arrival_time.strftime("%d.%m.%Y %H:%M") if v.arrival_time else "—"
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

    try:
        if settings.use_tls:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30)
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
        server.quit()
        return True, None
    except Exception as exc:
        return False, str(exc)


def build_monthly_csv(year: int, month: int) -> tuple[str, int]:
    """Return (csv_string, visitor_count) for the given year/month."""
    from app.models import Visitor  # lazy import avoids circular dependency

    start = datetime(year, month, 1, tzinfo=timezone.utc)
    last_day = monthrange(year, month)[1]
    end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

    visitors = (
        Visitor.query.filter(
            Visitor.arrival_time >= start,
            Visitor.arrival_time <= end,
        )
        .order_by(Visitor.arrival_time.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow([
        "Vorname", "Nachname", "Firma", "Ansprechpartner", "KFZ-Kennzeichen",
        "Ankunft", "Abfahrt", "Status",
        "F1_Erkältung", "F2_Durchfall", "F3_Lebensmittelvergiftung",
        "F4_Parasiten", "F5_HNO", "F6_Haut",
    ])

    def _q(val):
        if val is None:
            return ""
        return "Ja" if val else "Nein"

    for v in visitors:
        writer.writerow([
            v.first_name, v.last_name, v.company, v.contact_person,
            v.license_plate or "",
            v.arrival_time.strftime("%d.%m.%Y %H:%M") if v.arrival_time else "",
            v.departure_time.strftime("%d.%m.%Y %H:%M") if v.departure_time else "",
            "Vor Ort" if v.is_on_site else "Abgereist",
            _q(v.q1_flu), _q(v.q2_diarrhea), _q(v.q3_food_poisoning),
            _q(v.q4_parasites), _q(v.q5_ent), _q(v.q6_skin),
        ])

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

    try:
        if settings.use_tls:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30)
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
        server.quit()
        return True, None
    except Exception as exc:
        return False, str(exc)
