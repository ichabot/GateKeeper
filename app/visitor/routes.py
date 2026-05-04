"""Visitor-facing routes: check-in, check-out, info pages."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from flask import (
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.extensions import db
from app.models import HealthQuestion, StaticPage, Visitor, VisitorAnswer
from app.visitor import visitor_bp
from app.visitor.forms import CheckInForm, CheckOutForm


@visitor_bp.route("/")
def home():
    return render_template("visitor/home.html")


@visitor_bp.route("/checkin", methods=["GET", "POST"])
def checkin():
    form = CheckInForm()
    questions = (
        HealthQuestion.query
        .filter_by(active=True)
        .order_by(HealthQuestion.position)
        .all()
    )

    if form.validate_on_submit():
        # Collect answers from dynamic question fields
        answers = {}
        any_yes = False
        all_answered = True
        for q in questions:
            val = request.form.get(f"hq_{q.id}")
            if val not in ("yes", "no"):
                all_answered = False
            else:
                answers[q.id] = (val == "yes")
                if val == "yes":
                    any_yes = True

        if not all_answered:
            return render_template(
                "visitor/checkin.html", form=form, questions=questions,
                questions_error=True,
            )

        # Block check-in if any health question answered "yes"
        if any_yes:
            return render_template(
                "visitor/checkin.html", form=form, questions=questions,
                health_blocked=True,
            )

        pin = Visitor.generate_unique_pin()
        signature = request.form.get("signature_data") or None

        # Limit signature data size (max 500KB Base64)
        if signature and len(signature) > 512_000:
            signature = None

        visitor = Visitor(
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            company=form.company.data.strip(),
            contact_person=form.contact_person.data.strip(),
            license_plate=form.license_plate.data.strip() if form.license_plate.data else None,
            pin=pin,
            signature_data=signature,
            dsgvo_consent=True,
            hygiene_consent=True,
            safety_consent=True,
        )
        db.session.add(visitor)
        db.session.flush()  # Get visitor.id before adding answers

        # Store answers in new table
        for q_id, answer_val in answers.items():
            db.session.add(VisitorAnswer(
                visitor_id=visitor.id, question_id=q_id, answer=answer_val
            ))

        db.session.commit()
        return redirect(url_for("visitor.checkin_success", pin=pin))

    return render_template("visitor/checkin.html", form=form, questions=questions)


@visitor_bp.route("/checkin/success/<pin>")
def checkin_success(pin):
    return render_template("visitor/checkin_success.html", pin=pin)


# --- Simple brute-force protection for PIN checkout ---
_checkout_attempts = defaultdict(list)  # IP -> list of timestamps
_CHECKOUT_MAX_ATTEMPTS = 10
_CHECKOUT_LOCKOUT_SECONDS = 120


def _is_checkout_rate_limited(ip: str) -> bool:
    """Check if IP has exceeded checkout PIN attempt limit."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=_CHECKOUT_LOCKOUT_SECONDS)
    _checkout_attempts[ip] = [t for t in _checkout_attempts[ip] if t > cutoff]
    return len(_checkout_attempts[ip]) >= _CHECKOUT_MAX_ATTEMPTS


def _record_failed_checkout(ip: str):
    _checkout_attempts[ip].append(datetime.now(timezone.utc))


@visitor_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    form = CheckOutForm()
    if form.validate_on_submit():
        ip = request.remote_addr or "unknown"
        if _is_checkout_rate_limited(ip):
            lang = session.get("lang", "de")
            from app.translations import t
            flash(t("too_many_attempts", lang), "error")
            return render_template("visitor/checkout.html", form=form)

        pin = form.pin.data.strip()
        visitor = Visitor.query.filter_by(
            pin=pin, departure_time=None
        ).first()
        if visitor:
            visitor.departure_time = datetime.now(timezone.utc)
            db.session.commit()
            session["checkout_name"] = f"{visitor.first_name} {visitor.last_name}"
            # Clear attempts on success
            _checkout_attempts.pop(ip, None)
            return redirect(url_for("visitor.checkout_success"))
        else:
            _record_failed_checkout(ip)
            lang = session.get("lang", "de")
            from app.translations import t
            flash(t("invalid_pin", lang), "error")
    return render_template("visitor/checkout.html", form=form)


@visitor_bp.route("/checkout/success")
def checkout_success():
    name = session.pop("checkout_name", "")
    return render_template("visitor/checkout_success.html", name=name)


@visitor_bp.route("/info/<slug>")
def info_page(slug):
    page = StaticPage.query.filter_by(slug=slug).first_or_404()
    lang = session.get("lang", "de")
    title = getattr(page, f'title_{lang}', None) or page.title_de
    content = getattr(page, f'content_{lang}', None) or page.content_de
    return render_template(
        "visitor/info_page.html", title=title, content=content
    )


@visitor_bp.route("/lang/<lang_code>")
def set_language(lang_code):
    if lang_code in ("de", "en", "fr", "es"):
        session["lang"] = lang_code
    return redirect(request.referrer or url_for("visitor.home"))
