"""Authenticated admin API."""

import io
import os
import re
import time as _time
from collections import defaultdict, deque
from datetime import datetime, time, timedelta, timezone

from flask import Blueprint, Response, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from app import BERLIN_TZ, csv_safe, to_berlin, client_ip as _client_ip
from app.api import iso, logo_url, settings_public, visitor_to_dict
from app.audit import log_audit
from app.extensions import db

admin_bp = Blueprint("api_admin", __name__, url_prefix="/api/admin")

_LANGS = ("de", "en", "fr", "es")
_ALLOWED_LOGO_EXT = {".png", ".svg", ".jpg", ".jpeg", ".webp"}

# --- login rate limiter ----------------------------------------------------
_login_hits: dict = defaultdict(deque)


def _login_rate_limited() -> bool:
    key = _client_ip()
    now = _time.monotonic()
    dq = _login_hits[key]
    while dq and now - dq[0] > 60:
        dq.popleft()
    if len(dq) >= 5:
        return True
    dq.append(now)
    return False


@admin_bp.before_request
def _enforce_password_change():
    """Server-side enforcement of the forced first-login password change.

    The SPA gates the UI, but an attacker with default credentials could call
    the API directly — so while must_change_password is set, every admin
    endpoint except login/logout/session/password-change is rejected.
    """
    if not current_user.is_authenticated:
        return None  # @login_required handles unauthenticated access
    if not getattr(current_user, "must_change_password", False):
        return None
    allowed = {
        "api_admin.login", "api_admin.logout",
        "api_admin.whoami", "api_admin.account_password",
    }
    if request.endpoint in allowed:
        return None
    return jsonify({"error": "password_change_required"}), 403


def _parse_range(from_s, to_s):
    start = end = None
    try:
        if from_s:
            d = datetime.strptime(from_s, "%Y-%m-%d").date()
            start = datetime.combine(d, time(0, 0, 0), tzinfo=BERLIN_TZ).astimezone(timezone.utc)
        if to_s:
            d = datetime.strptime(to_s, "%Y-%m-%d").date()
            end = datetime.combine(d, time(23, 59, 59), tzinfo=BERLIN_TZ).astimezone(timezone.utc)
    except ValueError:
        pass
    return start, end


def _query_visitors(scope, from_s, to_s, text):
    from app.models import Visitor

    q = Visitor.query
    if scope == "live":
        q = q.filter(Visitor.departure_time.is_(None))
    start, end = _parse_range(from_s, to_s)
    if start:
        q = q.filter(Visitor.arrival_time >= start)
    if end:
        q = q.filter(Visitor.arrival_time <= end)
    if text:
        like = f"%{text.strip()}%"
        q = q.filter(or_(
            Visitor.first_name.ilike(like),
            Visitor.last_name.ilike(like),
            Visitor.company.ilike(like),
            Visitor.contact_person.ilike(like),
        ))
    order = Visitor.arrival_time.asc() if scope == "live" else Visitor.arrival_time.desc()
    return q.order_by(order).all()


# ===========================================================================
# Auth
# ===========================================================================
@admin_bp.post("/login")
def login():
    from app.models import AdminUser

    if _login_rate_limited():
        return jsonify({"error": "rate_limited"}), 429

    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = AdminUser.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid_credentials"}), 401

    login_user(user)
    log_audit("login", user=user.username)
    db.session.commit()
    return jsonify({"user": {
        "username": user.username,
        "must_change_password": user.must_change_password,
    }})


@admin_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})


@admin_bp.get("/session")
def whoami():
    if current_user.is_authenticated:
        return jsonify({"user": {
            "username": current_user.username,
            "must_change_password": current_user.must_change_password,
        }})
    return jsonify({"user": None}), 401


@admin_bp.post("/account/password")
@login_required
def account_password():
    """Change the logged-in admin's own password (verifies the current one).

    Also clears the must_change_password flag — this is the endpoint the forced
    first-login password change uses.
    """
    data = request.get_json(silent=True) or {}
    current = data.get("current_password") or ""
    new = data.get("new_password") or ""
    if not current_user.check_password(current):
        return jsonify({"error": "wrong_current"}), 403
    if len(new) < 8:
        return jsonify({"error": "weak_password"}), 400
    if new == current:
        return jsonify({"error": "same_password"}), 400
    current_user.set_password(new)
    current_user.must_change_password = False
    log_audit("password_change", detail=current_user.username)
    db.session.commit()
    return jsonify({"ok": True})


# ===========================================================================
# Visitors
# ===========================================================================
@admin_bp.get("/visitors")
@login_required
def visitors():
    scope = request.args.get("scope", "history")
    rows = _query_visitors(scope, request.args.get("from"), request.args.get("to"),
                           request.args.get("q"))
    return jsonify({"visitors": [visitor_to_dict(v) for v in rows]})


@admin_bp.get("/visitors/<int:vid>/signature")
@login_required
def visitor_signature(vid):
    from app.models import Visitor

    v = db.session.get(Visitor, vid)
    if not v:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"signature": v.signature_data or ""})


@admin_bp.post("/visitors/<int:vid>/checkout")
@login_required
def admin_checkout(vid):
    from app.models import Visitor

    v = db.session.get(Visitor, vid)
    if not v:
        return jsonify({"error": "not_found"}), 404
    if v.departure_time is None:
        v.departure_time = datetime.now(timezone.utc)
        log_audit("checkout_admin", detail=f"{v.first_name} {v.last_name}")
        db.session.commit()
    return jsonify({"ok": True, "visitor": visitor_to_dict(v)})


@admin_bp.delete("/visitors/<int:vid>")
@login_required
def delete_visitor(vid):
    from app.models import Visitor

    v = db.session.get(Visitor, vid)
    if not v:
        return jsonify({"error": "not_found"}), 404
    name = f"{v.first_name} {v.last_name}"
    db.session.delete(v)
    log_audit("delete", detail=name)
    db.session.commit()
    return jsonify({"ok": True})


# ===========================================================================
# Exports (CSV / PDF)
# ===========================================================================
def _build_csv(visitors_list) -> str:
    import csv as _csv
    from app.models import HealthQuestion

    questions = HealthQuestion.query.order_by(HealthQuestion.position).all()
    out = io.StringIO()
    w = _csv.writer(out, delimiter=";")
    header = ["Vorname", "Nachname", "Firma", "Gastgeber", "Kfz",
              "Datum", "Check-in", "Check-out", "Status", "PIN"]
    header += [q.text_de[:40] for q in questions]
    w.writerow(header)
    for v in visitors_list:
        arr = to_berlin(v.arrival_time) if v.arrival_time else None
        dep = to_berlin(v.departure_time) if v.departure_time else None
        row = [
            csv_safe(v.first_name), csv_safe(v.last_name), csv_safe(v.company),
            csv_safe(v.contact_person), csv_safe(v.license_plate or ""),
            arr.strftime("%d.%m.%Y") if arr else "",
            arr.strftime("%H:%M") if arr else "",
            dep.strftime("%H:%M") if dep else "",
            "Anwesend" if v.is_on_site else ("Nicht ausgecheckt" if v.auto_checked_out else "Ausgecheckt"),
            v.pin,
        ]
        answers = v.get_answers_for_csv()
        for q in questions:
            row.append(answers.get(q.short_key, ""))
        w.writerow(row)
    return out.getvalue()


@admin_bp.get("/export/csv")
@login_required
def export_csv():
    scope = request.args.get("scope", "history")
    rows = _query_visitors(scope, request.args.get("from"), request.args.get("to"),
                           request.args.get("q"))
    csv_text = _build_csv(rows)
    log_audit("export_csv", detail=f"{len(rows)} Einträge")
    db.session.commit()
    fname = "aktuell-anwesend.csv" if scope == "live" else "besucher-verlauf.csv"
    csv_text = "﻿" + csv_text  # UTF-8 BOM for Excel
    return Response(
        csv_text,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@admin_bp.get("/export/pdf")
@login_required
def export_pdf():
    from app.models import AppSettings
    from app.pdf import build_visitor_pdf

    scope = request.args.get("scope", "history")
    from_s, to_s = request.args.get("from"), request.args.get("to")
    rows = _query_visitors(scope, from_s, to_s, request.args.get("q"))

    s = db.session.get(AppSettings, 1)
    logo_file = None
    if s and s.logo_path:
        from flask import current_app
        candidate = os.path.join(current_app.config["UPLOAD_FOLDER"], s.logo_path)
        if os.path.isfile(candidate) and s.logo_path.lower().endswith((".png", ".jpg", ".jpeg")):
            logo_file = candidate  # reportlab raster images only

    period = " – ".join([p for p in (from_s, to_s) if p]) or "Alle"
    pdf_bytes = build_visitor_pdf(
        rows,
        title="Besucherverlauf" if scope != "live" else "Aktuell anwesend",
        period_label=period,
        logo_file=logo_file,
        company_name=s.company_name if s else "",
    )
    log_audit("export_pdf", detail=f"{len(rows)} Einträge")
    db.session.commit()
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="besucher-verlauf.pdf"'},
    )


# ===========================================================================
# Statistics
# ===========================================================================
@admin_bp.get("/stats")
@login_required
def stats():
    from app.models import Visitor

    now_utc = datetime.now(timezone.utc)
    now_berlin = to_berlin(now_utc)
    today = now_berlin.date()

    start7 = today - timedelta(days=6)
    start7_utc = datetime.combine(start7, time(0, 0, 0), tzinfo=BERLIN_TZ).astimezone(timezone.utc)
    recent = Visitor.query.filter(Visitor.arrival_time >= start7_utc).all()

    buckets = {(today - timedelta(days=i)): 0 for i in range(6, -1, -1)}
    for v in recent:
        d = to_berlin(v.arrival_time).date()
        if d in buckets:
            buckets[d] += 1
    bars = [{"date": d.isoformat(), "count": c} for d, c in sorted(buckets.items())]

    today_count = sum(1 for v in recent if to_berlin(v.arrival_time).date() == today)
    now_count = Visitor.query.filter(Visitor.departure_time.is_(None)).count()

    # average visit duration over completed visits in the last 90 days
    since = now_utc - timedelta(days=90)
    completed = Visitor.query.filter(
        Visitor.departure_time.isnot(None),
        Visitor.arrival_time >= since,
    ).all()
    avg_minutes = None
    if completed:
        total = 0
        for v in completed:
            arr = v.arrival_time.replace(tzinfo=timezone.utc) if v.arrival_time.tzinfo is None else v.arrival_time
            dep = v.departure_time.replace(tzinfo=timezone.utc) if v.departure_time.tzinfo is None else v.departure_time
            total += (dep - arr).total_seconds()
        avg_minutes = int(total / len(completed) / 60)

    return jsonify({
        "now": now_count,
        "today": today_count,
        "week": len(recent),
        "avg_minutes": avg_minutes,
        "bars": bars,
    })


# ===========================================================================
# Audit log
# ===========================================================================
@admin_bp.get("/audit")
@login_required
def audit():
    from app.models import AuditLog

    rows = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(300).all()
    return jsonify({"audit": [
        {"time": iso(a.created_at), "action": a.action, "detail": a.detail or "", "user": a.user or ""}
        for a in rows
    ]})


# ===========================================================================
# Info categories
# ===========================================================================
@admin_bp.get("/info")
@login_required
def info_list():
    from app.models import InfoCategory

    cats = InfoCategory.query.order_by(InfoCategory.position).all()
    return jsonify({"info": [c.to_dict() for c in cats]})


@admin_bp.put("/info/<key>")
@login_required
def info_update(key):
    from app.models import InfoCategory

    cat = InfoCategory.query.filter_by(key=key).first()
    if not cat:
        return jsonify({"error": "not_found"}), 404

    data = request.get_json(silent=True) or {}
    title = data.get("title") or {}
    body = data.get("body") or {}
    for lang in _LANGS:
        if lang in title:
            setattr(cat, f"title_{lang}", title[lang] or "")
        if cat.type == "art" and lang in body:
            setattr(cat, f"body_{lang}", body[lang] or "")
    if cat.type == "dir" and isinstance(data.get("entries"), list):
        cat.entries = data["entries"]
    cat.updated_at = datetime.now(timezone.utc)

    log_audit("info_saved", detail=key)
    db.session.commit()
    return jsonify({"info": cat.to_dict()})


# ===========================================================================
# Health questionnaire
# ===========================================================================
@admin_bp.get("/health")
@login_required
def health_get():
    from app.models import AppSettings, HealthQuestion

    s = db.session.get(AppSettings, 1)
    questions = HealthQuestion.query.order_by(HealthQuestion.position).all()
    return jsonify({
        "intro": {lang: getattr(s, f"health_intro_{lang}", "") if s else "" for lang in _LANGS},
        "questions": [q.to_dict() for q in questions],
    })


@admin_bp.put("/health")
@login_required
def health_put():
    from app.models import AppSettings, HealthQuestion

    data = request.get_json(silent=True) or {}
    s = db.session.get(AppSettings, 1)
    intro = data.get("intro") or {}
    if s:
        for lang in _LANGS:
            if lang in intro:
                setattr(s, f"health_intro_{lang}", intro[lang] or "")

    incoming = data.get("questions") or []
    existing = {q.id: q for q in HealthQuestion.query.all()}
    keep_ids = set()

    for idx, item in enumerate(incoming):
        text = item.get("text") or {}
        qid = item.get("id")
        row = existing.get(qid) if isinstance(qid, int) else None
        if row is None:
            short_key = (item.get("short_key") or "").strip() or _unique_key(idx)
            row = HealthQuestion(short_key=short_key, position=idx)
            db.session.add(row)
        row.position = idx
        row.active = bool(item.get("active", True))
        row.correct_answer = bool(item.get("correct_answer", False))
        for lang in _LANGS:
            setattr(row, f"text_{lang}", text.get(lang, "") or "")
        db.session.flush()
        keep_ids.add(row.id)

    # delete questions the admin removed (their answers cascade via VisitorAnswer FK)
    for qid, row in existing.items():
        if qid not in keep_ids:
            row.answers.delete(synchronize_session=False)  # remove dependent VisitorAnswer rows
            db.session.delete(row)

    log_audit("health_saved", detail=f"{len(incoming)} Fragen")
    db.session.commit()

    questions = HealthQuestion.query.order_by(HealthQuestion.position).all()
    return jsonify({
        "intro": {lang: getattr(s, f"health_intro_{lang}", "") if s else "" for lang in _LANGS},
        "questions": [q.to_dict() for q in questions],
    })


def _unique_key(idx: int) -> str:
    from app.models import HealthQuestion

    base = f"q{int(datetime.now(timezone.utc).timestamp())}_{idx}"
    candidate = base
    n = 0
    while HealthQuestion.query.filter_by(short_key=candidate).first():
        n += 1
        candidate = f"{base}_{n}"
    return candidate


# ===========================================================================
# Settings (branding / kiosk / SMTP / retention)
# ===========================================================================
@admin_bp.get("/settings")
@login_required
def settings_get():
    from app.models import AppSettings, SmtpSettings

    s = db.session.get(AppSettings, 1)
    smtp = db.session.get(SmtpSettings, 1)
    return jsonify({
        "branding": {
            "company_name": s.company_name if s else "",
            "logo_url": logo_url(s),
            "accent": s.accent if s else "blau",
        },
        "kiosk": {
            "kiosk_backdrop": s.kiosk_backdrop if s else "hell",
            "collect_plate": s.collect_plate if s else True,
            "auto_return_seconds": s.auto_return_seconds if s else 20,
        },
        "privacy": {"retention_days": s.retention_days if s else 90},
        "smtp": {
            "smtp_host": smtp.smtp_host if smtp else "",
            "smtp_port": smtp.smtp_port if smtp else 587,
            "smtp_user": smtp.smtp_user if smtp else "",
            "smtp_sender": smtp.smtp_sender if smtp else "",
            "smtp_recipients": smtp.smtp_recipients if smtp else "",
            "emergency_recipients": smtp.emergency_recipients if smtp else "",
            "use_tls": smtp.use_tls if smtp else True,
            "enabled": smtp.enabled if smtp else False,
            "password_set": bool(smtp.smtp_password) if smtp else False,
        },
    })


@admin_bp.put("/settings")
@login_required
def settings_put():
    from app.models import AppSettings, SmtpSettings

    data = request.get_json(silent=True) or {}
    s = db.session.get(AppSettings, 1)
    smtp = db.session.get(SmtpSettings, 1)

    branding = data.get("branding") or {}
    kiosk = data.get("kiosk") or {}
    privacy = data.get("privacy") or {}
    smtp_in = data.get("smtp") or {}

    if s:
        if "company_name" in branding:
            s.company_name = (branding["company_name"] or "").strip() or "GateKeeper"
        if "accent" in branding:
            a = (branding["accent"] or "").strip()
            # Accept a preset palette key or a custom #rrggbb hex; ignore garbage.
            if a in ("blau", "gruen", "violett", "anthrazit", "bernstein") or re.fullmatch(r"#[0-9a-fA-F]{6}", a):
                s.accent = a
        if "kiosk_backdrop" in kiosk:
            s.kiosk_backdrop = kiosk["kiosk_backdrop"]
        if "collect_plate" in kiosk:
            s.collect_plate = bool(kiosk["collect_plate"])
        if "auto_return_seconds" in kiosk:
            try:
                s.auto_return_seconds = max(5, min(60, int(kiosk["auto_return_seconds"])))
            except (TypeError, ValueError):
                pass
        if "retention_days" in privacy:
            try:
                s.retention_days = max(1, int(privacy["retention_days"]))
            except (TypeError, ValueError):
                pass
        s.updated_at = datetime.now(timezone.utc)

    if smtp:
        for field in ("smtp_host", "smtp_user", "smtp_sender", "smtp_recipients",
                      "emergency_recipients"):
            if field in smtp_in:
                setattr(smtp, field, smtp_in[field] or "")
        if "smtp_port" in smtp_in:
            try:
                smtp.smtp_port = int(smtp_in["smtp_port"])
            except (TypeError, ValueError):
                pass
        if "use_tls" in smtp_in:
            smtp.use_tls = bool(smtp_in["use_tls"])
        if "enabled" in smtp_in:
            smtp.enabled = bool(smtp_in["enabled"])
        # password only overwritten when a non-empty value is supplied
        if smtp_in.get("smtp_password"):
            smtp.smtp_password = smtp_in["smtp_password"]
        smtp.updated_at = datetime.now(timezone.utc)

    log_audit("settings_saved")
    db.session.commit()
    return settings_get()


@admin_bp.post("/settings/logo")
@login_required
def upload_logo():
    from flask import current_app
    from app.models import AppSettings

    file = request.files.get("logo")
    if not file or not file.filename:
        return jsonify({"error": "no_file"}), 400
    ext = os.path.splitext(secure_filename(file.filename))[1].lower()
    if ext not in _ALLOWED_LOGO_EXT:
        return jsonify({"error": "bad_type"}), 400

    filename = f"logo{ext}"
    dest = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    # remove any previous logo files with a different extension
    s = db.session.get(AppSettings, 1)
    if s and s.logo_path and s.logo_path != filename:
        old = os.path.join(current_app.config["UPLOAD_FOLDER"], s.logo_path)
        if os.path.isfile(old):
            try:
                os.remove(old)
            except OSError:
                pass
    file.save(dest)
    if s:
        s.logo_path = filename
        s.updated_at = datetime.now(timezone.utc)
    log_audit("settings_saved", detail="Logo")
    db.session.commit()
    return jsonify({"logo_url": logo_url(s)})


@admin_bp.delete("/settings/logo")
@login_required
def delete_logo():
    from flask import current_app
    from app.models import AppSettings

    s = db.session.get(AppSettings, 1)
    if s and s.logo_path:
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], s.logo_path)
        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass
        s.logo_path = None
        db.session.commit()
    return jsonify({"logo_url": ""})


# ===========================================================================
# Emergency + SMTP test
# ===========================================================================
@admin_bp.post("/emergency")
@login_required
def emergency():
    from app.mail import send_emergency_report
    from app.models import SmtpSettings, Visitor

    smtp = db.session.get(SmtpSettings, 1)
    present = Visitor.query.filter(Visitor.departure_time.is_(None)).count()
    if not smtp or not smtp.smtp_host or not smtp.emergency_recipients:
        return jsonify({"error": "smtp_incomplete"}), 400

    ok, err = send_emergency_report(smtp)
    log_audit("emergency", detail=f"{present} anwesend")
    db.session.commit()
    if ok:
        return jsonify({"ok": True, "present": present})
    return jsonify({"error": "send_failed", "detail": err}), 502


@admin_bp.post("/smtp/test")
@login_required
def smtp_test():
    from app.mail import _smtp_connect
    from app.models import SmtpSettings

    smtp = db.session.get(SmtpSettings, 1)
    if not smtp or not smtp.smtp_host:
        return jsonify({"error": "smtp_incomplete"}), 400
    server = None
    try:
        server = _smtp_connect(smtp)
        return jsonify({"ok": True})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "connect_failed", "detail": str(exc)}), 502
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass


# ===========================================================================
# Visitor profiles ("Besucherausweise") — DSGVO management
# ===========================================================================
@admin_bp.get("/profiles")
@login_required
def profiles_list():
    from app.models import VisitorProfile

    text = (request.args.get("q") or "").strip()
    q = VisitorProfile.query
    if text:
        like = f"%{text}%"
        q = q.filter(or_(
            VisitorProfile.first_name.ilike(like),
            VisitorProfile.last_name.ilike(like),
            VisitorProfile.company.ilike(like),
            VisitorProfile.contact_person.ilike(like),
        ))
    rows = q.order_by(VisitorProfile.last_seen_at.desc()).limit(200).all()
    return jsonify({"profiles": [p.to_dict() for p in rows]})


@admin_bp.delete("/profiles/<int:pid>")
@login_required
def profiles_delete(pid):
    from app.models import VisitorProfile

    p = db.session.get(VisitorProfile, pid)
    if not p:
        return jsonify({"error": "not_found"}), 404
    name = f"{p.first_name} {p.last_name}"
    db.session.delete(p)
    log_audit("profile_delete", detail=name)
    db.session.commit()
    return jsonify({"ok": True})


# ===========================================================================
# Admin users (accounts)
# ===========================================================================
def _user_dict(u) -> dict:
    return {
        "id": u.id,
        "username": u.username,
        "created_at": iso(u.created_at),
        "is_self": u.id == current_user.id,
    }


@admin_bp.get("/users")
@login_required
def users_list():
    from app.models import AdminUser

    rows = AdminUser.query.order_by(AdminUser.username).all()
    return jsonify({"users": [_user_dict(u) for u in rows]})


@admin_bp.post("/users")
@login_required
def users_create():
    from app.models import AdminUser

    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if len(username) < 3:
        return jsonify({"error": "bad_username"}), 400
    if len(password) < 8:
        return jsonify({"error": "weak_password"}), 400
    if AdminUser.query.filter_by(username=username).first():
        return jsonify({"error": "exists"}), 409

    u = AdminUser(username=username)
    u.set_password(password)
    # The creating admin knows this password — the new user must pick their own.
    u.must_change_password = True
    db.session.add(u)
    log_audit("user_create", detail=username)
    db.session.commit()
    return jsonify({"user": _user_dict(u)}), 201


@admin_bp.put("/users/<int:uid>/password")
@login_required
def users_password(uid):
    from app.models import AdminUser

    data = request.get_json(silent=True) or {}
    password = data.get("password") or ""
    if len(password) < 8:
        return jsonify({"error": "weak_password"}), 400
    u = db.session.get(AdminUser, uid)
    if not u:
        return jsonify({"error": "not_found"}), 404
    u.set_password(password)
    # A reset password is known to the resetting admin — force the target to
    # choose their own (unless they reset it for themselves).
    if u.id != current_user.id:
        u.must_change_password = True
    log_audit("user_password", detail=u.username)
    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.delete("/users/<int:uid>")
@login_required
def users_delete(uid):
    from app.models import AdminUser

    u = db.session.get(AdminUser, uid)
    if not u:
        return jsonify({"error": "not_found"}), 404
    if u.id == current_user.id:
        return jsonify({"error": "self"}), 400
    if AdminUser.query.count() <= 1:
        return jsonify({"error": "last_user"}), 400
    name = u.username
    db.session.delete(u)
    log_audit("user_delete", detail=name)
    db.session.commit()
    return jsonify({"ok": True})


# ===========================================================================
# Content export / import
# ===========================================================================
@admin_bp.get("/content/export")
@login_required
def content_export():
    import json as _json
    from app.content_io import export_content

    include_logo = request.args.get("logo", "1") != "0"
    data = export_content(include_logo=include_logo)
    stamp = to_berlin(datetime.now(timezone.utc)).strftime("%Y%m%d")
    payload = _json.dumps(data, ensure_ascii=False, indent=2)
    return Response(
        payload,
        mimetype="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="gatekeeper-content-{stamp}.json"'},
    )


@admin_bp.post("/content/import")
@login_required
def content_import():
    import json as _json
    from app.content_io import import_content

    mode = request.args.get("mode", "replace")
    preview = request.args.get("preview", "0") == "1"

    # Accept either an uploaded file or a raw JSON body.
    raw = None
    if "file" in request.files:
        raw = request.files["file"].read().decode("utf-8", errors="replace")
    else:
        raw = request.get_data(as_text=True)

    try:
        data = _json.loads(raw) if raw else None
        result = import_content(data, mode=mode, preview=preview)
    except ValueError as exc:
        return jsonify({"error": "invalid", "detail": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        db.session.rollback()
        return jsonify({"error": "import_failed", "detail": str(exc)}), 400

    if not preview:
        log_audit("content_import", detail=f"mode={mode}")
        db.session.commit()
    return jsonify(result)
