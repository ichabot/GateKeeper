"""Audit-trail helper."""

from flask import request
from flask_login import current_user

from app.extensions import db


# Known action codes (for reference / consistency).
ACTIONS = (
    "login",
    "logout",
    "checkout_admin",
    "delete",
    "export_csv",
    "export_pdf",
    "emergency",
    "settings_saved",
    "info_saved",
    "health_saved",
    "content_import",
    "user_create",
    "user_password",
    "user_delete",
)


def _client_ip() -> str | None:
    # Honour a single proxy hop if present (user runs their own reverse proxy).
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote_addr


def log_audit(action: str, detail: str | None = None, user: str | None = None) -> None:
    """Append an audit entry. Commit is the caller's responsibility unless
    ``commit`` is desired — here we add + flush so it participates in the
    surrounding transaction and is persisted on the next commit."""
    from app.models import AuditLog

    if user is None:
        try:
            user = current_user.username if current_user.is_authenticated else None
        except Exception:
            user = None

    entry = AuditLog(action=action, detail=detail, user=user, ip=_client_ip())
    db.session.add(entry)
