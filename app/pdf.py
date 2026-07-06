"""PDF visitor report (reportlab) — a clean, branded history export."""

import io
import os
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from app import to_berlin

NAVY = colors.HexColor("#14233f")
SOFT = colors.HexColor("#eef1f6")
GREY = colors.HexColor("#69768f")
GREEN = colors.HexColor("#1f9d6b")


def _fmt(dt, pattern):
    if dt is None:
        return "—"
    return to_berlin(dt).strftime(pattern)


def build_visitor_pdf(
    visitors,
    *,
    title="Besucherverlauf",
    period_label="",
    logo_file=None,
    company_name="",
) -> bytes:
    """Return PDF bytes for the given visitor rows."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        title=title,
    )

    title_style = ParagraphStyle(
        "gk_title", fontName="Helvetica-Bold", fontSize=17, textColor=NAVY, leading=20,
    )
    meta_style = ParagraphStyle(
        "gk_meta", fontName="Helvetica", fontSize=9, textColor=GREY, leading=12,
    )
    cell_style = ParagraphStyle(
        "gk_cell", fontName="Helvetica", fontSize=8.5, textColor=NAVY, leading=10.5,
    )
    head_style = ParagraphStyle(
        "gk_head", fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.white, leading=10.5,
    )

    elements = []

    # --- Header band (logo + title + meta) --------------------------------
    generated = to_berlin(datetime.now(timezone.utc)).strftime("%d.%m.%Y %H:%M")
    meta_lines = []
    if company_name:
        meta_lines.append(f"<b>{escape(company_name)}</b>")
    if period_label:
        meta_lines.append(f"Zeitraum: {escape(period_label)}")
    meta_lines.append(f"Erstellt: {generated} Uhr · {len(visitors)} Einträge")
    meta_para = Paragraph("<br/>".join(meta_lines), meta_style)

    logo_cell = ""
    if logo_file and os.path.isfile(logo_file):
        try:
            logo_cell = Image(logo_file, width=22 * mm, height=22 * mm, kind="proportional")
        except Exception:
            logo_cell = ""

    header_tbl = Table(
        [[logo_cell, [Paragraph(title, title_style), Spacer(1, 3), meta_para]]],
        colWidths=[26 * mm, None],
    )
    header_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_tbl)
    elements.append(Spacer(1, 8))

    # --- Data table -------------------------------------------------------
    headers = ["Name", "Firma", "Gastgeber", "Kfz", "Datum", "Check-in", "Check-out", "Status"]
    data = [[Paragraph(h, head_style) for h in headers]]

    for v in visitors:
        # Paragraph parses XML-ish markup — escape visitor-supplied text, or a
        # kiosk visitor named "<b" would crash every PDF export.
        name = f"{v.first_name} {v.last_name}".strip()
        status = "Anwesend" if v.is_on_site else "Ausgecheckt"
        row = [
            Paragraph(escape(name), cell_style),
            Paragraph(escape(v.company or "—"), cell_style),
            Paragraph(escape(v.contact_person or "—"), cell_style),
            Paragraph(escape(v.license_plate or "—"), cell_style),
            Paragraph(_fmt(v.arrival_time, "%d.%m.%Y"), cell_style),
            Paragraph(_fmt(v.arrival_time, "%H:%M"), cell_style),
            Paragraph(_fmt(v.departure_time, "%H:%M"), cell_style),
            Paragraph(status, cell_style),
        ]
        data.append(row)

    if len(data) == 1:
        data.append([Paragraph("Keine Einträge für die aktuelle Auswahl.", cell_style)]
                    + ["" for _ in range(len(headers) - 1)])

    col_widths = [46 * mm, 40 * mm, 38 * mm, 24 * mm, 24 * mm, 22 * mm, 22 * mm, 26 * mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7dde8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
    ]
    table.setStyle(TableStyle(style))
    elements.append(table)

    doc.build(elements)
    return buf.getvalue()
