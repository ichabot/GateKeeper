"""WSGI entry point for GateKeeper."""

from app import create_app

application = create_app()
