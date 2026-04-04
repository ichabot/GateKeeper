"""Admin routes: login, dashboard, export, page editing, health questions."""

import csv
import io
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone

from flask import (
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from app import to_berlin
from app.admin import admin_bp
from app.admin.forms import EditPageForm, FilterForm, HealthQuestionForm, LoginForm, SmtpSettingsForm
from app.extensions import db
from app.mail import send_monthly_report, send_emergency_report
from app.models import AdminUser, HealthQuestion, SmtpSettings, StaticPage, Visitor


def _fmt_berlin(dt):
    """Format a datetime in Berlin timezone as dd.mm.yyyy HH:MM."""
    if dt is None:
        return ""
    return to_berlin(dt).strftime("%d.%m.%Y %H:%M")

# --- Simple brute-force protection (in-memory) ---
_login_attempts = defaultdict(list)  # IP -> list of timestamps
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 60


def _is_rate_limited(ip: str) -> bool:
    """Check if IP has exceeded login attempt limit."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=_LOCKOUT_SECONDS)
    # Clean old attempts
    _login_attempts[ip] = [t for t in _login_attempts[ip] if t > cutoff]
    return len(_login_attempts[ip]) >= _MAX_ATTEMPTS


def _record_failed_attempt(ip: str):
    _login_attempts[ip].append(datetime.now(timezone.utc))


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    ip = request.remote_addr or "unknown"
    form = LoginForm()

    if form.validate_on_submit():
        if _is_rate_limited(ip):
            flash("Zu viele Anmeldeversuche. Bitte warten Sie eine Minute.", "error")
            return render_template("admin/login.html", form=form)

        user = AdminUser.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            # Clear attempts on successful login
            _login_attempts.pop(ip, None)
            login_user(user)
            return redirect(url_for("admin.dashboard"))

        _record_failed_attempt(ip)
        remaining = _MAX_ATTEMPTS - len(_login_attempts.get(ip, []))
        if remaining > 0:
            flash(f"Ungültige Anmeldedaten. ({remaining} Versuch(e) verbleibend)", "error")
        else:
            flash("Zu viele Anmeldeversuche. Bitte warten Sie eine Minute.", "error")

    return render_template("admin/login.html", form=form)


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("visitor.home"))


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    form = FilterForm(request.args)
    query = Visitor.query

    # Status filter
    status = request.args.get("status", "all")
    if status == "on_site":
        query = query.filter(Visitor.departure_time.is_(None))
    elif status == "departed":
        query = query.filter(Visitor.departure_time.isnot(None))
    elif status == "missed":
        today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min).replace(tzinfo=timezone.utc)
        query = query.filter(
            Visitor.departure_time.is_(None),
            Visitor.arrival_time < today_start,
        )

    # Date range filter - default to today if no date is provided
    date_from = form.date_from.data
    date_to = form.date_to.data
    if date_from is None and date_to is None and not request.args:
        date_from = datetime.now(timezone.utc).date()
        form.date_from.data = date_from

    if date_from:
        query = query.filter(
            Visitor.arrival_time >= datetime.combine(date_from, time.min).replace(
                tzinfo=timezone.utc
            )
        )
    if date_to:
        query = query.filter(
            Visitor.arrival_time
            <= datetime.combine(date_to, time.max).replace(tzinfo=timezone.utc)
        )

    # Text search
    search = request.args.get("search", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Visitor.first_name.ilike(like),
                Visitor.last_name.ilike(like),
                Visitor.company.ilike(like),
                Visitor.contact_person.ilike(like),
            )
        )

    visitors = query.order_by(Visitor.arrival_time.desc()).all()
    on_site_count = Visitor.query.filter(Visitor.departure_time.is_(None)).count()

    return render_template(
        "admin/dashboard.html",
        visitors=visitors,
        form=form,
        on_site_count=on_site_count,
    )


@admin_bp.route("/export")
@login_required
def export_csv():
    """Export filtered visitor list as CSV with dynamic health question columns."""
    query = Visitor.query

    status = request.args.get("status", "all")
    if status == "on_site":
        query = query.filter(Visitor.departure_time.is_(None))
    elif status == "departed":
        query = query.filter(Visitor.departure_time.isnot(None))

    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    if date_from:
        query = query.filter(
            Visitor.arrival_time >= datetime.fromisoformat(date_from)
        )
    if date_to:
        dt = datetime.fromisoformat(date_to)
        query = query.filter(
            Visitor.arrival_time <= dt.replace(hour=23, minute=59, second=59)
        )

    visitors = query.order_by(Visitor.arrival_time.desc()).all()

    # Get all health questions for CSV headers (active + inactive for completeness)
    questions = HealthQuestion.query.order_by(HealthQuestion.position).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    # Dynamic header
    header = [
        "Vorname", "Nachname", "Firma", "Ansprechpartner", "KFZ-Kennzeichen",
        "Ankunft", "Abfahrt", "Status",
    ]
    for q in questions:
        header.append(q.text_de[:50])  # Truncate long question texts
    writer.writerow(header)

    for v in visitors:
        row = [
            v.first_name,
            v.last_name,
            v.company,
            v.contact_person,
            v.license_plate or "",
            _fmt_berlin(v.arrival_time),
            _fmt_berlin(v.departure_time),
            "Vor Ort" if v.is_on_site else "Abgereist",
        ]
        answers = v.get_answers_for_csv()
        for q in questions:
            row.append(answers.get(q.short_key, ""))
        writer.writerow(row)

    response = Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=besucher_export.csv"
        },
    )
    return response


@admin_bp.route("/pages")
@login_required
def pages_list():
    pages = StaticPage.query.order_by(StaticPage.slug).all()
    return render_template("admin/pages_list.html", pages=pages)


# --- Health Questions Management ---

@admin_bp.route("/questions")
@login_required
def questions_list():
    questions = HealthQuestion.query.order_by(HealthQuestion.position).all()
    return render_template("admin/questions_list.html", questions=questions)


@admin_bp.route("/questions/new", methods=["GET", "POST"])
@login_required
def question_new():
    form = HealthQuestionForm()
    if form.validate_on_submit():
        # Auto-generate position (append at end)
        max_pos = db.session.query(db.func.max(HealthQuestion.position)).scalar() or 0
        q = HealthQuestion(
            position=max_pos + 1,
            text_de=form.text_de.data.strip(),
            text_en=form.text_en.data.strip(),
            short_key=form.short_key.data.strip().lower().replace(" ", "_"),
            active=form.active.data,
        )
        db.session.add(q)
        db.session.commit()
        flash("Frage erstellt.", "success")
        return redirect(url_for("admin.questions_list"))
    return render_template("admin/question_edit.html", form=form, is_new=True)


@admin_bp.route("/questions/<int:question_id>", methods=["GET", "POST"])
@login_required
def question_edit(question_id):
    q = db.session.get(HealthQuestion, question_id)
    if not q:
        flash("Frage nicht gefunden.", "error")
        return redirect(url_for("admin.questions_list"))

    form = HealthQuestionForm(obj=q)
    if form.validate_on_submit():
        q.text_de = form.text_de.data.strip()
        q.text_en = form.text_en.data.strip()
        q.short_key = form.short_key.data.strip().lower().replace(" ", "_")
        q.active = form.active.data
        q.position = form.position.data
        db.session.commit()
        flash("Frage gespeichert.", "success")
        return redirect(url_for("admin.questions_list"))
    return render_template("admin/question_edit.html", form=form, question=q, is_new=False)


@admin_bp.route("/questions/<int:question_id>/delete", methods=["POST"])
@login_required
def question_delete(question_id):
    q = db.session.get(HealthQuestion, question_id)
    if q:
        db.session.delete(q)
        db.session.commit()
        flash("Frage gelöscht.", "success")
    return redirect(url_for("admin.questions_list"))


# --- SMTP Settings ---

@admin_bp.route("/smtp", methods=["GET", "POST"])
@login_required
def smtp_settings():
    settings = db.session.get(SmtpSettings, 1)
    if settings is None:
        settings = SmtpSettings(id=1)
        db.session.add(settings)
        db.session.commit()

    form = SmtpSettingsForm(obj=settings)
    if form.validate_on_submit():
        settings.smtp_host = form.smtp_host.data.strip()
        settings.smtp_port = form.smtp_port.data
        settings.smtp_user = form.smtp_user.data.strip()
        if form.smtp_password.data:
            settings.smtp_password = form.smtp_password.data
        settings.smtp_sender = form.smtp_sender.data.strip()
        settings.smtp_recipients = form.smtp_recipients.data.strip()
        settings.emergency_recipients = form.emergency_recipients.data.strip() if form.emergency_recipients.data else ""
        settings.use_tls = form.use_tls.data
        settings.enabled = form.enabled.data
        settings.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        flash("SMTP-Einstellungen gespeichert.", "success")
        return redirect(url_for("admin.smtp_settings"))

    return render_template("admin/smtp_settings.html", form=form, settings=settings)


@admin_bp.route("/smtp/test", methods=["POST"])
@login_required
def smtp_test():
    settings = db.session.get(SmtpSettings, 1)
    if not settings or not settings.smtp_host:
        flash("Bitte zuerst SMTP-Einstellungen speichern.", "error")
        return redirect(url_for("admin.smtp_settings"))

    now = datetime.now(timezone.utc)
    ok, err = send_monthly_report(settings, now.year, now.month)
    if ok:
        flash(f"Test-E-Mail erfolgreich gesendet an: {settings.smtp_recipients}", "success")
    else:
        flash(f"Fehler beim Senden: {err}", "error")
    return redirect(url_for("admin.smtp_settings"))


@admin_bp.route("/smtp/send-report", methods=["POST"])
@login_required
def smtp_send_report():
    settings = db.session.get(SmtpSettings, 1)
    if not settings or not settings.smtp_host:
        flash("SMTP nicht konfiguriert.", "error")
        return redirect(url_for("admin.smtp_settings"))

    now = datetime.now(timezone.utc)
    if now.month == 1:
        year, month = now.year - 1, 12
    else:
        year, month = now.year, now.month - 1

    month_names = [
        "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember",
    ]
    ok, err = send_monthly_report(settings, year, month)
    if ok:
        flash(f"Bericht {month_names[month - 1]} {year} erfolgreich gesendet.", "success")
    else:
        flash(f"Fehler beim Senden: {err}", "error")
    return redirect(url_for("admin.smtp_settings"))


@admin_bp.route("/emergency-send", methods=["POST"])
@login_required
def emergency_send():
    settings = db.session.get(SmtpSettings, 1)
    if not settings or not settings.smtp_host:
        flash("SMTP nicht konfiguriert. Bitte zuerst E-Mail-Einstellungen speichern.", "error")
        return redirect(url_for("admin.dashboard"))
    if not settings.emergency_recipients:
        flash("Keine Notfall-Empfänger konfiguriert. Bitte in den E-Mail-Einstellungen eintragen.", "error")
        return redirect(url_for("admin.dashboard"))

    ok, err = send_emergency_report(settings)
    if ok:
        flash(f"Notfall-E-Mail erfolgreich gesendet an: {settings.emergency_recipients}", "success")
    else:
        flash(f"Fehler beim Senden der Notfall-E-Mail: {err}", "error")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/pages/<slug>", methods=["GET", "POST"])
@login_required
def edit_page(slug):
    page = StaticPage.query.filter_by(slug=slug).first_or_404()
    form = EditPageForm(obj=page)
    if form.validate_on_submit():
        page.title_de = form.title_de.data
        page.title_en = form.title_en.data
        page.content_de = form.content_de.data
        page.content_en = form.content_en.data
        page.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        flash("Seite gespeichert.", "success")
        return redirect(url_for("admin.pages_list"))
    return render_template("admin/edit_page.html", form=form, page=page)
