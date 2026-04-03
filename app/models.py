"""SQLAlchemy database models for GateKeeper."""

import random
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, login_manager


class Visitor(db.Model):
    __tablename__ = "visitors"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(200), nullable=False)
    pin = db.Column(db.String(4), nullable=False)
    arrival_time = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    departure_time = db.Column(db.DateTime(timezone=True), nullable=True)
    signature_data = db.Column(db.Text, nullable=True)  # Base64 PNG data URL
    license_plate = db.Column(db.String(20), nullable=True)
    dsgvo_consent = db.Column(db.Boolean, nullable=False, default=False)
    hygiene_consent = db.Column(db.Boolean, nullable=False, default=False)
    safety_consent = db.Column(db.Boolean, nullable=False, default=False)
    # Health questionnaire answers (True = Ja/Yes, False = Nein/No)
    q1_flu = db.Column(db.Boolean, nullable=True)
    q2_diarrhea = db.Column(db.Boolean, nullable=True)
    q3_food_poisoning = db.Column(db.Boolean, nullable=True)
    q4_parasites = db.Column(db.Boolean, nullable=True)
    q5_ent = db.Column(db.Boolean, nullable=True)
    q6_skin = db.Column(db.Boolean, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    @property
    def is_on_site(self) -> bool:
        return self.departure_time is None

    @property
    def missed_checkout(self) -> bool:
        """Visitor still 'on site' but arrival was before today (forgot to check out)."""
        if self.departure_time is not None:
            return False
        if self.arrival_time is None:
            return False
        now = datetime.now(timezone.utc)
        return self.arrival_time.date() < now.date()

    @staticmethod
    def generate_unique_pin() -> str:
        """Generate a 4-digit PIN unique among currently active visitors."""
        active_pins = {
            row[0]
            for row in db.session.query(Visitor.pin)
            .filter(Visitor.departure_time.is_(None))
            .all()
        }
        for _ in range(100):
            pin = f"{random.randint(0, 9999):04d}"
            if pin not in active_pins:
                return pin
        raise RuntimeError("Unable to generate unique PIN")

    def __repr__(self) -> str:
        return f"<Visitor {self.first_name} {self.last_name} ({self.company})>"


class AdminUser(db.Model, UserMixin):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(AdminUser, int(user_id))


class SmtpSettings(db.Model):
    """Single-row table for SMTP configuration (id always = 1)."""

    __tablename__ = "smtp_settings"

    id = db.Column(db.Integer, primary_key=True)
    smtp_host = db.Column(db.String(200), nullable=False, default="")
    smtp_port = db.Column(db.Integer, nullable=False, default=587)
    smtp_user = db.Column(db.String(200), nullable=False, default="")
    smtp_password = db.Column(db.String(200), nullable=False, default="")
    smtp_sender = db.Column(db.String(200), nullable=False, default="")
    smtp_recipients = db.Column(db.Text, nullable=False, default="")
    emergency_recipients = db.Column(db.Text, nullable=False, default="")
    use_tls = db.Column(db.Boolean, nullable=False, default=True)
    enabled = db.Column(db.Boolean, nullable=False, default=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class StaticPage(db.Model):
    __tablename__ = "static_pages"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    title_de = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)
    content_de = db.Column(db.Text, nullable=False, default="")
    content_en = db.Column(db.Text, nullable=False, default="")
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
