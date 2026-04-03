"""Flask extensions initialization."""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
babel = Babel()
csrf = CSRFProtect()

login_manager.login_view = "admin.login"
login_manager.login_message_category = "warning"
