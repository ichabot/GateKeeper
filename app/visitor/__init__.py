"""Visitor blueprint for public-facing pages."""

from flask import Blueprint

visitor_bp = Blueprint(
    "visitor",
    __name__,
    template_folder="../templates/visitor",
)

from app.visitor import routes  # noqa: E402, F401
