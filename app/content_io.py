"""Export / import of editable content as JSON.

Purpose (user request): back up all editorial content before a software update
and restore it afterwards. Deliberately excludes visitor data and the SMTP
password.
"""

import base64
import os
from datetime import datetime, timezone

from app.extensions import db

SCHEMA_VERSION = 1
_LANGS = ("de", "en", "fr", "es")


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
def export_content(include_logo: bool = True) -> dict:
    from app.models import AppSettings, HealthQuestion, InfoCategory

    s = db.session.get(AppSettings, 1)
    questions = HealthQuestion.query.order_by(HealthQuestion.position).all()
    cats = InfoCategory.query.order_by(InfoCategory.position).all()

    branding = {
        "company_name": s.company_name if s else "",
        "accent": s.accent if s else "blau",
        "kiosk_backdrop": s.kiosk_backdrop if s else "hell",
        "collect_plate": s.collect_plate if s else True,
        "auto_return_seconds": s.auto_return_seconds if s else 20,
        "retention_days": s.retention_days if s else 90,
    }

    logo_b64 = None
    if include_logo and s and s.logo_path:
        from flask import current_app
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], s.logo_path)
        if os.path.isfile(path):
            with open(path, "rb") as fh:
                logo_b64 = {
                    "filename": s.logo_path,
                    "data": base64.b64encode(fh.read()).decode("ascii"),
                }

    return {
        "schema": SCHEMA_VERSION,
        "app": "gatekeeper",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "branding": branding,
        "logo": logo_b64,
        "health": {
            "intro": {lang: getattr(s, f"health_intro_{lang}", "") if s else "" for lang in _LANGS},
            "questions": [q.to_dict() for q in questions],
        },
        "info": [c.to_dict() for c in cats],
    }


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------
def _set(obj, attr, value, mode):
    """Apply a value honouring the import mode ('replace' or 'fill')."""
    if value is None:
        return False
    if mode == "fill" and getattr(obj, attr, None):
        return False
    if getattr(obj, attr, None) == value:
        return False
    setattr(obj, attr, value)
    return True


def _summary(data: dict) -> dict:
    health = data.get("health", {}) or {}
    return {
        "schema": data.get("schema"),
        "exported_at": data.get("exported_at"),
        "info_categories": len(data.get("info", []) or []),
        "questions": len(health.get("questions", []) or []),
        "has_branding": bool(data.get("branding")),
        "has_logo": bool(data.get("logo")),
    }


def import_content(data: dict, mode: str = "replace", preview: bool = False) -> dict:
    """Validate and (unless *preview*) apply an exported content bundle."""
    if not isinstance(data, dict):
        raise ValueError("Ungültiges Dateiformat.")
    if data.get("schema") != SCHEMA_VERSION:
        raise ValueError(f"Nicht unterstützte Schema-Version: {data.get('schema')!r}.")
    if mode not in ("replace", "fill"):
        raise ValueError("Ungültiger Modus.")

    summary = _summary(data)
    if preview:
        summary["preview"] = True
        return summary

    from app.models import AppSettings, HealthQuestion, InfoCategory

    changed = 0
    s = db.session.get(AppSettings, 1)

    # --- Branding ---------------------------------------------------------
    branding = data.get("branding") or {}
    if s:
        for key in ("company_name", "accent", "kiosk_backdrop"):
            if key in branding and _set(s, key, branding[key], mode):
                changed += 1
        for key in ("collect_plate",):
            if key in branding:
                if not (mode == "fill"):  # booleans have no "empty" concept
                    if getattr(s, key) != bool(branding[key]):
                        setattr(s, key, bool(branding[key]))
                        changed += 1
        for key in ("auto_return_seconds", "retention_days"):
            if key in branding and isinstance(branding[key], int):
                if mode == "replace" and getattr(s, key) != branding[key]:
                    setattr(s, key, branding[key])
                    changed += 1

    # --- Health intro + questions ----------------------------------------
    health = data.get("health") or {}
    intro = health.get("intro") or {}
    if s:
        for lang in _LANGS:
            if lang in intro and _set(s, f"health_intro_{lang}", intro[lang], mode):
                changed += 1

    for q in health.get("questions", []) or []:
        key = q.get("short_key")
        if not key:
            continue
        row = HealthQuestion.query.filter_by(short_key=key).first()
        text = q.get("text") or {}
        if not row:
            max_pos = db.session.query(db.func.max(HealthQuestion.position)).scalar() or 0
            row = HealthQuestion(
                short_key=key,
                position=q.get("position", max_pos + 1),
                active=q.get("active", True),
                correct_answer=bool(q.get("correct_answer", False)),
                text_de=text.get("de", ""), text_en=text.get("en", ""),
                text_fr=text.get("fr", ""), text_es=text.get("es", ""),
            )
            db.session.add(row)
            changed += 1
            continue
        for lang in _LANGS:
            if lang in text and _set(row, f"text_{lang}", text[lang], mode):
                changed += 1
        if mode == "replace":
            if row.correct_answer != bool(q.get("correct_answer", False)):
                row.correct_answer = bool(q.get("correct_answer", False))
                changed += 1

    # --- Info categories --------------------------------------------------
    for c in data.get("info", []) or []:
        key = c.get("key")
        if not key:
            continue
        row = InfoCategory.query.filter_by(key=key).first()
        title = c.get("title") or {}
        body = c.get("body") or {}
        if not row:
            row = InfoCategory(
                key=key,
                type=c.get("type", "art"),
                icon=c.get("icon", "info"),
                accent=c.get("accent", "#2f6fed"),
                position=c.get("position", 99),
                active=c.get("active", True),
            )
            db.session.add(row)
            changed += 1
        for lang in _LANGS:
            if lang in title and _set(row, f"title_{lang}", title[lang], mode):
                changed += 1
            if lang in body and _set(row, f"body_{lang}", body[lang], mode):
                changed += 1
        if "entries" in c and isinstance(c["entries"], list):
            if mode == "replace" or not row.entries:
                row.entries = c["entries"]
                changed += 1

    db.session.commit()
    summary["applied"] = True
    summary["changed_fields"] = changed
    summary["mode"] = mode
    return summary
