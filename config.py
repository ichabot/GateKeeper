"""Flask configuration classes."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LANGUAGES = ["de", "en"]
    BABEL_DEFAULT_LOCALE = "de"
    ADMIN_DEFAULT_PASSWORD = os.environ.get("ADMIN_DEFAULT_PASSWORD", "admin")


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

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

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
