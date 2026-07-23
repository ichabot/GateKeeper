"""JSON API blueprints for GateKeeper."""

from datetime import timezone


def iso(dt):
    """Serialize a datetime as ISO-8601 UTC (treats naive as UTC)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def visitor_to_dict(v) -> dict:
    return {
        "id": v.id,
        "first_name": v.first_name,
        "last_name": v.last_name,
        "name": f"{v.first_name} {v.last_name}".strip(),
        "company": v.company,
        "host": v.contact_person,
        "plate": v.license_plate or "",
        "pin": v.pin,
        "arrival": iso(v.arrival_time),
        "departure": iso(v.departure_time),
        "on_site": v.is_on_site,
        "auto_checked_out": v.auto_checked_out,
        "missed_checkout": v.missed_checkout,
        "has_signature": bool(v.signature_data),
    }


def logo_url(settings) -> str:
    if settings and settings.logo_path:
        return "/uploads/" + settings.logo_path
    return ""


def settings_public(settings) -> dict:
    """Branding + kiosk config exposed to the kiosk (no secrets)."""
    if not settings:
        return {}
    return {
        "company_name": settings.company_name,
        "logo_url": logo_url(settings),
        "accent": settings.accent,
        "kiosk_backdrop": settings.kiosk_backdrop,
        "collect_plate": settings.collect_plate,
        "auto_return_seconds": settings.auto_return_seconds,
        "idle_timeout_seconds": settings.idle_timeout_seconds,
    }


def register_api(app, csrf):
    from app.api.public import public_bp
    from app.api.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    # Public kiosk endpoints are intentionally CSRF-exempt (unauthenticated
    # kiosk actions, protected instead by rate limiting). Admin endpoints keep
    # CSRF protection and require the X-CSRFToken header.
    csrf.exempt(public_bp)
