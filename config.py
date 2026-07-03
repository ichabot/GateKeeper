"""Flask configuration classes."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_DEFAULT_PASSWORD = os.environ.get("ADMIN_DEFAULT_PASSWORD", "admin")

    # Uploads (logo). Absolute path resolved against instance/ in the app factory
    # when left as a bare name. Overridable via UPLOAD_FOLDER env var.
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    # Max request body — covers signature PNG (~500 KB) + logo (~2 MB) with headroom.
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024

    # Session cookie hardening (SPA is same-origin with the API).
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Set SESSION_COOKIE_SECURE=1 in production behind TLS (also required for
    # the iPad Wake Lock API). Left off by default so plain-HTTP VM testing works.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "").lower() in (
        "1", "true", "yes",
    )

    # CSRF: token has no fixed expiry (long-lived kiosk admin sessions), and we
    # don't enforce the strict Referer check because the app runs behind the
    # user's own reverse proxy. Protection still relies on the X-CSRFToken
    # header + SameSite=Lax cookie.
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # Allow insecure default key in development only
    if not BaseConfig.SECRET_KEY:
        SECRET_KEY = "dev-insecure-key-do-not-use-in-production"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///gatekeeper.db",
    )


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///gatekeeper.db",
    )

    @classmethod
    def init_app(cls, app):
        if not cls.SECRET_KEY:
            print("FATAL: SECRET_KEY not set. Refusing to start in production.", file=sys.stderr)
            print("Set SECRET_KEY in .env or as environment variable.", file=sys.stderr)
            sys.exit(1)


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
