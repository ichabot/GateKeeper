"""WTForms for visitor check-in and check-out."""

from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class CheckInForm(FlaskForm):
    first_name = StringField(
        "Vorname",
        validators=[DataRequired(), Length(max=100)],
    )
    last_name = StringField(
        "Nachname",
        validators=[DataRequired(), Length(max=100)],
    )
    company = StringField(
        "Firma",
        validators=[DataRequired(), Length(max=200)],
    )
    contact_person = StringField(
        "Ansprechpartner",
        validators=[DataRequired(), Length(max=200)],
    )
    license_plate = StringField(
        "KFZ-Kennzeichen",
        validators=[Optional(), Length(max=20)],
    )
    signature_data = HiddenField("Unterschrift")

    # Health questions are now dynamic (loaded from DB, rendered in template).
    # Answers are read directly from request.form in the route.

    dsgvo_consent = BooleanField(
        "Datenschutz",
        validators=[DataRequired(message="Bitte stimmen Sie der Datenschutzerklärung zu.")],
    )
    hygiene_consent = BooleanField(
        "Hygieneregeln",
        validators=[DataRequired(message="Bitte bestätigen Sie die Hygieneregeln.")],
    )
    safety_consent = BooleanField(
        "Sicherheitshinweise",
        validators=[DataRequired(message="Bitte bestätigen Sie die Sicherheits-/Verhaltenshinweise.")],
    )
    submit = SubmitField("Einchecken")


class CheckOutForm(FlaskForm):
    pin = StringField(
        "PIN",
        validators=[DataRequired(), Length(min=4, max=6)],
    )
    submit = SubmitField("Auschecken")
