"""Visitor-facing routes: check-in, check-out, info pages."""

from datetime import datetime, timezone

from flask import (
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.extensions import db
from app.models import StaticPage, Visitor
from app.visitor import visitor_bp
from app.visitor.forms import CheckInForm, CheckOutForm


@visitor_bp.route("/")
def home():
    return render_template("visitor/home.html")


@visitor_bp.route("/checkin", methods=["GET", "POST"])
def checkin():
    form = CheckInForm()
    if form.validate_on_submit():
        # Server-side safety check: refuse check-in if any health question answered "yes"
        if any(f.data == "yes" for f in [form.q1, form.q2, form.q3, form.q4, form.q5, form.q6]):
            return render_template("visitor/checkin.html", form=form, health_blocked=True)

        pin = Visitor.generate_unique_pin()
        # Read signature from raw form data (manual hidden input, not WTForms)
        signature = request.form.get("signature_data") or None
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
            q1_flu=(form.q1.data == "yes"),
            q2_diarrhea=(form.q2.data == "yes"),
            q3_food_poisoning=(form.q3.data == "yes"),
            q4_parasites=(form.q4.data == "yes"),
            q5_ent=(form.q5.data == "yes"),
            q6_skin=(form.q6.data == "yes"),
        )
        db.session.add(visitor)
        db.session.commit()
        return redirect(url_for("visitor.checkin_success", pin=pin))
    return render_template("visitor/checkin.html", form=form)


@visitor_bp.route("/checkin/success/<pin>")
def checkin_success(pin):
    return render_template("visitor/checkin_success.html", pin=pin)


@visitor_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    form = CheckOutForm()
    if form.validate_on_submit():
        pin = form.pin.data.strip()
        visitor = Visitor.query.filter_by(
            pin=pin, departure_time=None
        ).first()
        if visitor:
            visitor.departure_time = datetime.now(timezone.utc)
            db.session.commit()
            return redirect(
                url_for(
                    "visitor.checkout_success",
                    name=f"{visitor.first_name} {visitor.last_name}",
                )
            )
        else:
            flash("Ungültiger PIN. Bitte versuchen Sie es erneut.", "error")
    return render_template("visitor/checkout.html", form=form)


@visitor_bp.route("/checkout/success")
def checkout_success():
    name = request.args.get("name", "")
    return render_template("visitor/checkout_success.html", name=name)


@visitor_bp.route("/info/<slug>")
def info_page(slug):
    page = StaticPage.query.filter_by(slug=slug).first_or_404()
    lang = session.get("lang", "de")
    title = page.title_en if lang == "en" else page.title_de
    content = page.content_en if lang == "en" else page.content_de
    return render_template(
        "visitor/info_page.html", title=title, content=content
    )


@visitor_bp.route("/lang/<lang_code>")
def set_language(lang_code):
    if lang_code in ("de", "en"):
        session["lang"] = lang_code
    return redirect(request.referrer or url_for("visitor.home"))
