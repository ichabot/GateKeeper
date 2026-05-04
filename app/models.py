"""SQLAlchemy database models for GateKeeper."""

import random
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, login_manager


class HealthQuestion(db.Model):
    """Admin-configurable health questionnaire questions."""

    __tablename__ = "health_questions"

    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    text_de = db.Column(db.Text, nullable=False)
    text_en = db.Column(db.Text, nullable=False, default="")
    text_fr = db.Column(db.Text, nullable=False, default="")
    text_es = db.Column(db.Text, nullable=False, default="")
    short_key = db.Column(db.String(50), nullable=False, unique=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    answers = db.relationship("VisitorAnswer", back_populates="question", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<HealthQuestion {self.position}: {self.short_key}>"


class VisitorAnswer(db.Model):
    """Visitor answers to health questionnaire questions."""

    __tablename__ = "visitor_answers"

    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.Integer, db.ForeignKey("visitors.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("health_questions.id"), nullable=False)
    answer = db.Column(db.Boolean, nullable=False)

    visitor = db.relationship("Visitor", back_populates="health_answers")
    question = db.relationship("HealthQuestion", back_populates="answers")

    __table_args__ = (
        db.UniqueConstraint("visitor_id", "question_id", name="uq_visitor_question"),
    )


class Visitor(db.Model):
    __tablename__ = "visitors"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(200), nullable=False)
    pin = db.Column(db.String(6), nullable=False)
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

    # Legacy columns kept for backward compatibility with old data.
    # New visitors use the VisitorAnswer table instead.
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

    health_answers = db.relationship(
        "VisitorAnswer", back_populates="visitor", lazy="selectin",
        cascade="all, delete-orphan",
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

    @property
    def has_positive_answer(self) -> bool:
        """True if any health question was answered with Yes."""
        # Check new dynamic answers first
        if self.health_answers:
            return any(a.answer for a in self.health_answers)
        # Fallback to legacy columns
        legacy = [self.q1_flu, self.q2_diarrhea, self.q3_food_poisoning,
                  self.q4_parasites, self.q5_ent, self.q6_skin]
        return any(v is True for v in legacy)

    @property
    def has_any_answers(self) -> bool:
        """True if visitor has any health questionnaire answers."""
        if self.health_answers:
            return True
        legacy = [self.q1_flu, self.q2_diarrhea, self.q3_food_poisoning,
                  self.q4_parasites, self.q5_ent, self.q6_skin]
        return any(v is not None for v in legacy)

    def get_answers_display(self) -> list[dict]:
        """Return list of {question_de, question_en, question_fr, question_es, answer} for display."""
        if self.health_answers:
            return [
                {
                    "text_de": a.question.text_de,
                    "text_en": a.question.text_en,
                    "text_fr": a.question.text_fr,
                    "text_es": a.question.text_es,
                    "answer": a.answer,
                }
                for a in sorted(self.health_answers, key=lambda a: a.question.position)
            ]
        # Legacy fallback
        legacy_qs = [
            ("Erkältungskrankheiten", "Flu diseases", self.q1_flu),
            ("Durchfall / Erbrechen", "Diarrhoea / vomiting", self.q2_diarrhea),
            ("Lebensmittelvergiftung", "Food poisoning", self.q3_food_poisoning),
            ("Parasitäre Infektionen", "Parasitic infections", self.q4_parasites),
            ("HNO-Infektionen", "ENT infections", self.q5_ent),
            ("Hauterkrankungen / Wunden", "Skin diseases / wounds", self.q6_skin),
        ]
        return [
            {"text_de": de, "text_en": en, "answer": val}
            for de, en, val in legacy_qs
            if val is not None
        ]

    def get_answers_for_csv(self) -> dict[str, str]:
        """Return {short_key: 'Ja'/'Nein'/''} for CSV export."""
        if self.health_answers:
            result = {}
            for a in sorted(self.health_answers, key=lambda a: a.question.position):
                result[a.question.short_key] = "Ja" if a.answer else "Nein"
            return result
        # Legacy
        def _q(val):
            if val is None:
                return ""
            return "Ja" if val else "Nein"
        return {
            "flu": _q(self.q1_flu),
            "diarrhea": _q(self.q2_diarrhea),
            "food_poisoning": _q(self.q3_food_poisoning),
            "parasites": _q(self.q4_parasites),
            "ent": _q(self.q5_ent),
            "skin": _q(self.q6_skin),
        }

    @staticmethod
    def generate_unique_pin() -> str:
        """Generate a 4-digit PIN unique among currently active visitors.

        Falls back to 5-digit and then 6-digit PINs if 4-digit space is
        exhausted (>~9000 concurrent visitors, highly unlikely).
        """
        active_pins = {
            row[0]
            for row in db.session.query(Visitor.pin)
            .filter(Visitor.departure_time.is_(None))
            .all()
        }
        for digits in (4, 5, 6):
            upper = 10**digits
            for _ in range(200):
                pin = f"{random.randint(0, upper - 1):0{digits}d}"
                if pin not in active_pins:
                    return pin
        raise RuntimeError("Unable to generate unique PIN — too many active visitors")

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
    title_fr = db.Column(db.String(200), nullable=False, default="")
    title_es = db.Column(db.String(200), nullable=False, default="")
    content_de = db.Column(db.Text, nullable=False, default="")
    content_en = db.Column(db.Text, nullable=False, default="")
    content_fr = db.Column(db.Text, nullable=False, default="")
    content_es = db.Column(db.Text, nullable=False, default="")
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
