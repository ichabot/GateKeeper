"""SQLAlchemy database models for GateKeeper."""

import json
import secrets
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
    # Expected ("correct") answer. False = "No" is correct (default).
    # Check-in is blocked when a visitor's answer differs from this value.
    correct_answer = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    answers = db.relationship("VisitorAnswer", back_populates="question", lazy="dynamic")

    def text_for(self, lang: str) -> str:
        """Return the question text for a language with fallback to EN then DE."""
        for try_lang in (lang, "en", "de"):
            val = getattr(self, f"text_{try_lang}", None)
            if val:
                return val
        return ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "position": self.position,
            "short_key": self.short_key,
            "active": self.active,
            "correct_answer": self.correct_answer,
            "text": {
                "de": self.text_de,
                "en": self.text_en,
                "fr": self.text_fr,
                "es": self.text_es,
            },
        }

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

    # Token of the returning-visitor pass ("Besucherausweis") used/created at
    # check-in, if any — lets the visitor also check out by scanning their pass.
    profile_token = db.Column(db.String(24), nullable=True, index=True)

    # Set True by the nightly `auto-checkout` job when a visitor never checked
    # out themselves — surfaced in the admin views as "Nicht ausgecheckt".
    auto_checked_out = db.Column(db.Boolean, nullable=False, default=False)

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
        from app import BERLIN_TZ
        now_berlin = datetime.now(BERLIN_TZ)
        arrival_berlin = self.arrival_time.astimezone(BERLIN_TZ) if self.arrival_time.tzinfo else self.arrival_time
        return arrival_berlin.date() < now_berlin.date()

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
                # secrets, not random: the PIN is the check-out credential.
                pin = f"{secrets.randbelow(upper):0{digits}d}"
                if pin not in active_pins:
                    return pin
        raise RuntimeError("Unable to generate unique PIN — too many active visitors")

    def __repr__(self) -> str:
        return f"<Visitor {self.first_name} {self.last_name} ({self.company})>"


class VisitorProfile(db.Model):
    """Opt-in returning-visitor profile ("Besucherausweis").

    Stores only the reusable master data (never health answers) so a returning
    visitor can be pre-filled by scanning a QR that encodes the token. The
    token is the credential printed in the QR; it is looked up offline by the
    kiosk (the visitor's phone needs no network).
    """

    __tablename__ = "visitor_profiles"

    # Unambiguous alphabet (no 0/O/1/I) for tokens that may be typed by hand.
    _ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(24), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(200), nullable=False, default="")
    license_plate = db.Column(db.String(20), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_seen_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    @classmethod
    def generate_token(cls) -> str:
        for _ in range(50):
            tok = "".join(secrets.choice(cls._ALPHABET) for _ in range(10))
            # Checkout routes all-digit codes to the PIN lookup — skip the rare
            # purely numeric token so a hand-typed pass code always resolves.
            if tok.isdigit():
                continue
            if not cls.query.filter_by(token=tok).first():
                return tok
        raise RuntimeError("Unable to generate unique profile token")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "token": self.token,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "name": f"{self.first_name} {self.last_name}".strip(),
            "company": self.company,
            "host": self.contact_person or "",
            "plate": self.license_plate or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
        }

    def __repr__(self) -> str:
        return f"<VisitorProfile {self.token} {self.first_name} {self.last_name}>"


class AdminUser(db.Model, UserMixin):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # Forces a password change on next login (set for the seeded default admin
    # and any account still using the configured default password).
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)
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
    """DEPRECATED — kept for backward compatibility / migration source.

    Info content now lives in :class:`InfoCategory`. This table is no longer
    read by the running app; it is retained so a redesign migration can pull
    admin-edited content out of it and so no data is dropped.
    """

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


class AppSettings(db.Model):
    """Single-row table (id=1) for branding, kiosk config and retention."""

    __tablename__ = "app_settings"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False, default="GateKeeper")
    logo_path = db.Column(db.String(255), nullable=True)  # relative to UPLOAD_FOLDER
    accent = db.Column(db.String(20), nullable=False, default="blau")
    retention_days = db.Column(db.Integer, nullable=False, default=90)
    # Kiosk configuration (formerly hard-coded artifact props)
    kiosk_backdrop = db.Column(db.String(20), nullable=False, default="hell")  # hell/anthrazit/schlicht
    collect_plate = db.Column(db.Boolean, nullable=False, default=True)
    auto_return_seconds = db.Column(db.Integer, nullable=False, default=20)
    # Questionnaire intro text per language
    health_intro_de = db.Column(db.Text, nullable=False, default="")
    health_intro_en = db.Column(db.Text, nullable=False, default="")
    health_intro_fr = db.Column(db.Text, nullable=False, default="")
    health_intro_es = db.Column(db.Text, nullable=False, default="")
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def health_intro_for(self, lang: str) -> str:
        for try_lang in (lang, "en", "de"):
            val = getattr(self, f"health_intro_{try_lang}", None)
            if val:
                return val
        return ""


class AuditLog(db.Model):
    """Append-only audit trail of admin-relevant actions."""

    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    action = db.Column(db.String(50), nullable=False)  # code, see app.audit.ACTIONS
    detail = db.Column(db.String(255), nullable=True)
    user = db.Column(db.String(80), nullable=True)
    ip = db.Column(db.String(64), nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.created_at:%Y-%m-%d %H:%M}>"


class InfoCategory(db.Model):
    """Kiosk information content — either a directory (dir) or an article (art)."""

    __tablename__ = "info_categories"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(40), unique=True, nullable=False)
    type = db.Column(db.String(8), nullable=False, default="art")  # 'dir' | 'art'
    icon = db.Column(db.String(20), nullable=False, default="info")
    accent = db.Column(db.String(20), nullable=False, default="#2f6fed")
    position = db.Column(db.Integer, nullable=False, default=0)
    active = db.Column(db.Boolean, nullable=False, default=True)

    title_de = db.Column(db.String(200), nullable=False, default="")
    title_en = db.Column(db.String(200), nullable=False, default="")
    title_fr = db.Column(db.String(200), nullable=False, default="")
    title_es = db.Column(db.String(200), nullable=False, default="")

    # Article body (Markdown) per language — used when type == 'art'
    body_de = db.Column(db.Text, nullable=False, default="")
    body_en = db.Column(db.Text, nullable=False, default="")
    body_fr = db.Column(db.Text, nullable=False, default="")
    body_es = db.Column(db.Text, nullable=False, default="")

    # Directory entries as JSON — used when type == 'dir'
    # [{"label": {"de","en","fr","es"}, "value": "..."}]
    entries_json = db.Column(db.Text, nullable=False, default="[]")

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    @property
    def entries(self) -> list:
        try:
            data = json.loads(self.entries_json or "[]")
            return data if isinstance(data, list) else []
        except (ValueError, TypeError):
            return []

    @entries.setter
    def entries(self, value: list) -> None:
        self.entries_json = json.dumps(value or [], ensure_ascii=False)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "type": self.type,
            "icon": self.icon,
            "accent": self.accent,
            "position": self.position,
            "active": self.active,
            "title": {
                "de": self.title_de,
                "en": self.title_en,
                "fr": self.title_fr,
                "es": self.title_es,
            },
            "body": {
                "de": self.body_de,
                "en": self.body_en,
                "fr": self.body_fr,
                "es": self.body_es,
            },
            "entries": self.entries,
        }
