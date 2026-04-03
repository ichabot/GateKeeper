"""WTForms for admin area."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, NumberRange, Optional


class LoginForm(FlaskForm):
    username = StringField("Benutzername", validators=[DataRequired()])
    password = PasswordField("Passwort", validators=[DataRequired()])
    submit = SubmitField("Anmelden")


class FilterForm(FlaskForm):
    class Meta:
        csrf = False

    date_from = DateField("Von", validators=[Optional()])
    date_to = DateField("Bis", validators=[Optional()])
    status = SelectField(
        "Status",
        choices=[
            ("all", "Alle"),
            ("on_site", "Vor Ort"),
            ("departed", "Abgereist"),
            ("missed", "Kein Checkout"),
        ],
        default="all",
    )
    search = StringField("Suche", validators=[Optional()])
    submit = SubmitField("Filtern")


class SmtpSettingsForm(FlaskForm):
    smtp_host = StringField("SMTP Host", validators=[DataRequired()])
    smtp_port = IntegerField(
        "SMTP Port",
        validators=[DataRequired(), NumberRange(1, 65535)],
        default=587,
    )
    smtp_user = StringField("Benutzername (SMTP-Auth)", validators=[DataRequired()])
    smtp_password = PasswordField(
        "Passwort (leer lassen = unverändertes Passwort beibehalten)"
    )
    smtp_sender = StringField("Absender-Adresse (Von)", validators=[DataRequired()])
    smtp_recipients = StringField(
        "Empfänger-Adressen (kommagetrennt)", validators=[DataRequired()]
    )
    emergency_recipients = StringField(
        "Notfall-Empfänger (kommagetrennt)", validators=[Optional()]
    )
    use_tls = BooleanField("STARTTLS verwenden (empfohlen, Port 587)")
    enabled = BooleanField("Monatlicher Versand aktiv (automatisch per Cronjob)")
    submit = SubmitField("Einstellungen speichern")


class EditPageForm(FlaskForm):
    title_de = StringField("Titel (DE)", validators=[DataRequired()])
    title_en = StringField("Titel (EN)", validators=[DataRequired()])
    content_de = TextAreaField("Inhalt (DE)")
    content_en = TextAreaField("Inhalt (EN)")
    submit = SubmitField("Speichern")
