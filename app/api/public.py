"""Public (unauthenticated) kiosk API: bootstrap, check-in, check-out."""

import time as _time
from collections import defaultdict, deque
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_wtf.csrf import generate_csrf
from sqlalchemy import func, or_

from app.extensions import db
from app.api import iso, settings_public

public_bp = Blueprint("api_public", __name__, url_prefix="/api")

_SIG_MAX = 700_000  # max base64 signature length (~500 KB PNG)

# --- tiny in-memory rate limiter (per worker) ------------------------------
_hits: dict = defaultdict(deque)


def _rate_limited(key: str, limit: int, window: float) -> bool:
    now = _time.monotonic()
    dq = _hits[key]
    while dq and now - dq[0] > window:
        dq.popleft()
    if len(dq) >= limit:
        return True
    dq.append(now)
    return False


def _client_ip() -> str:
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote_addr or "?"


@public_bp.get("/csrf")
def csrf_token():
    return jsonify({"csrf_token": generate_csrf()})


@public_bp.get("/bootstrap")
def bootstrap():
    from app.models import AppSettings, HealthQuestion, InfoCategory

    s = db.session.get(AppSettings, 1)
    questions = (
        HealthQuestion.query.filter_by(active=True)
        .order_by(HealthQuestion.position)
        .all()
    )
    cats = (
        InfoCategory.query.filter_by(active=True)
        .order_by(InfoCategory.position)
        .all()
    )

    return jsonify({
        "settings": settings_public(s),
        "health": {
            "intro": {
                "de": s.health_intro_de if s else "",
                "en": s.health_intro_en if s else "",
                "fr": s.health_intro_fr if s else "",
                "es": s.health_intro_es if s else "",
            },
            "questions": [q.to_dict() for q in questions],
        },
        "info": [c.to_dict() for c in cats],
    })


def _normalize_pass_code(code: str) -> str:
    """Strip an optional GKP: prefix from a scanned/typed visitor-pass code."""
    code = (code or "").strip()
    if code.upper().startswith("GKP:"):
        code = code[4:]
    return code.strip()


@public_bp.post("/checkin")
def checkin():
    from app.models import HealthQuestion, Visitor, VisitorAnswer, VisitorProfile

    if _rate_limited(f"checkin:{_client_ip()}", limit=20, window=120):
        return jsonify({"error": "rate_limited"}), 429

    data = request.get_json(silent=True) or {}
    first = (data.get("first_name") or "").strip()
    last = (data.get("last_name") or "").strip()
    company = (data.get("company") or "").strip()
    host = (data.get("host") or data.get("contact_person") or "").strip()
    plate = (data.get("plate") or data.get("license_plate") or "").strip().upper()
    answers = data.get("answers") or {}
    consent = data.get("consent") or {}
    signature = data.get("signature") or ""
    save_profile = bool(data.get("save_profile"))
    profile_token = _normalize_pass_code(data.get("profile_token") or "")

    # Required fields
    if not (first and last and company and host):
        return jsonify({"error": "missing_fields"}), 400

    # Prevent a duplicate active check-in: the same person is already on site
    # (not yet checked out). Match on name + company (case-insensitive), or on
    # the returning-visitor pass token when checking in via a pass. A visitor
    # who has already checked out may check in again the same day.
    dup_conds = [
        (func.lower(Visitor.first_name) == first.lower())
        & (func.lower(Visitor.last_name) == last.lower())
        & (func.lower(Visitor.company) == company.lower())
    ]
    if profile_token:
        dup_conds.append(Visitor.profile_token == profile_token.upper())
    already = (
        Visitor.query
        .filter(Visitor.departure_time.is_(None), or_(*dup_conds))
        .first()
    )
    if already:
        return jsonify({"error": "already_checked_in"}), 409

    # Consents (all three mandatory)
    if not (consent.get("ds") and consent.get("hy") and consent.get("sf")):
        return jsonify({"error": "consent_required"}), 400

    # Health questionnaire: every active question must be answered and must
    # match its correct_answer, otherwise check-in is blocked.
    questions = (
        HealthQuestion.query.filter_by(active=True)
        .order_by(HealthQuestion.position)
        .all()
    )
    parsed = {}
    for q in questions:
        raw = answers.get(str(q.id), answers.get(q.id))
        if raw is None:
            return jsonify({"error": "health_incomplete"}), 400
        parsed[q.id] = bool(raw)
        if bool(raw) != bool(q.correct_answer):
            return jsonify({"error": "health_blocked"}), 422

    # Signature required
    if not signature.startswith("data:image/") or len(signature) > _SIG_MAX:
        return jsonify({"error": "signature_required"}), 400

    pin = Visitor.generate_unique_pin()
    visitor = Visitor(
        first_name=first, last_name=last, company=company, contact_person=host,
        license_plate=plate or None, pin=pin,
        signature_data=signature,
        dsgvo_consent=True, hygiene_consent=True, safety_consent=True,
        arrival_time=datetime.now(timezone.utc),
    )
    db.session.add(visitor)
    db.session.flush()  # assign visitor.id

    for q in questions:
        db.session.add(VisitorAnswer(
            visitor_id=visitor.id, question_id=q.id, answer=parsed[q.id]
        ))

    # --- returning-visitor profile ("Besucherausweis") --------------------
    # Only ever stores master data, never health answers. Created only on
    # explicit opt-in (save_profile); refreshed when the visitor came in via
    # an existing pass (profile_token).
    now = datetime.now(timezone.utc)
    prof = None
    if profile_token:
        prof = VisitorProfile.query.filter_by(token=profile_token).first()
    if prof is None and save_profile:
        prof = VisitorProfile(token=VisitorProfile.generate_token())
        db.session.add(prof)
    if prof is not None:
        prof.first_name = first
        prof.last_name = last
        prof.company = company
        prof.contact_person = host
        prof.license_plate = plate or None
        prof.last_seen_at = now
        # Link this visit to the pass so it can be checked out by scanning it.
        visitor.profile_token = prof.token

    db.session.commit()

    resp = {"pin": pin}
    if prof is not None:
        # Scannable QR encoding the returning-visitor pass token (offline).
        from app.qr import qr_svg
        resp["pass_token"] = prof.token
        resp["pass_qr"] = qr_svg(f"GKP:{prof.token}")
    return jsonify(resp), 201


@public_bp.post("/profile/lookup")
def profile_lookup():
    """Look up a returning visitor by their pass token (offline credential)."""
    from app.models import VisitorProfile

    if _rate_limited(f"lookup:{_client_ip()}", limit=30, window=120):
        return jsonify({"error": "rate_limited"}), 429

    data = request.get_json(silent=True) or {}
    token = _normalize_pass_code(data.get("code") or "")
    if not token:
        return jsonify({"error": "invalid"}), 400

    prof = VisitorProfile.query.filter_by(token=token).first()
    if not prof:
        return jsonify({"error": "not_found"}), 404

    return jsonify({
        "token": prof.token,
        "first_name": prof.first_name,
        "last_name": prof.last_name,
        "company": prof.company,
        "host": prof.contact_person or "",
        "plate": prof.license_plate or "",
    })


@public_bp.post("/checkout")
def checkout():
    from app.models import Visitor

    if _rate_limited(f"checkout:{_client_ip()}", limit=10, window=120):
        return jsonify({"error": "rate_limited"}), 429

    data = request.get_json(silent=True) or {}
    raw = (data.get("code") or data.get("pin") or "").strip()
    if not raw:
        return jsonify({"error": "invalid_pin"}), 400

    # A visitor pass ("Besucherausweis") is GKP:-prefixed / alphanumeric, a PIN
    # is purely numeric — detect which was entered or scanned and match the
    # matching active visit.
    if raw.upper().startswith("GKP:") or not raw.isdigit():
        token = _normalize_pass_code(raw).upper()
        cond = (Visitor.profile_token == token)
    else:
        cond = (Visitor.pin == raw)

    visitor = (
        Visitor.query.filter(cond, Visitor.departure_time.is_(None))
        .order_by(Visitor.arrival_time.desc())
        .first()
    )
    if not visitor:
        return jsonify({"error": "invalid_pin"}), 404

    now = datetime.now(timezone.utc)
    visitor.departure_time = now
    db.session.commit()

    arrival = visitor.arrival_time
    if arrival and arrival.tzinfo is None:
        arrival = arrival.replace(tzinfo=timezone.utc)
    minutes = int((now - arrival).total_seconds() // 60) if arrival else 0

    return jsonify({
        "ok": True,
        "minutes": max(0, minutes),
        "arrival": iso(visitor.arrival_time),
        "departure": iso(visitor.departure_time),
    })
