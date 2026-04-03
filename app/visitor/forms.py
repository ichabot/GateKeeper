"""WTForms for visitor check-in and check-out."""

from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, BooleanField, SubmitField, RadioField
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

    # Health questionnaire (6 yes/no questions)
    q1 = RadioField(
        "q1",
        choices=[("yes", "Ja"), ("no", "Nein")],
        validators=[DataRequired(message="Bitte beantworten Sie alle Fragen.")],
    )
    q2 = RadioField(
        "q2",
        choices=[("yes", "Ja"), ("no", "Nein")],
        validators=[DataRequired(message="Bitte beantworten Sie alle Fragen.")],
    )
    q3 = RadioField(
        "q3",
        choices=[("yes", "Ja"), ("no", "Nein")],
        validators=[DataRequired(message="Bitte beantworten Sie alle Fragen.")],
    )
    q4 = RadioField(
        "q4",
        choices=[("yes", "Ja"), ("no", "Nein")],
        validators=[DataRequired(message="Bitte beantworten Sie alle Fragen.")],
    )
    q5 = RadioField(
        "q5",
        choices=[("yes", "Ja"), ("no", "Nein")],
        validators=[DataRequired(message="Bitte beantworten Sie alle Fragen.")],
    )
    q6 = RadioField(
        "q6",
        choices=[("yes", "Ja"), ("no", "Nein")],
        validators=[DataRequired(message="Bitte beantworten Sie alle Fragen.")],
    )

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
        validators=[DataRequired(), Length(min=4, max=4)],
    )
    submit = SubmitField("Auschecken")
