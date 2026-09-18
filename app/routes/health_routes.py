"""Readiness without credentials, environment details or financial side effects."""
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from flask import jsonify
from sqlalchemy import text

from app import db


def register_health_routes(app):
    root = Path(__file__).resolve().parents[2]
    heads = ScriptDirectory.from_config(Config(str(root / "alembic.ini"))).get_heads()

    @app.get("/healthz")
    def readiness():
        ready = False
        try:
            with db.engine.connect() as connection:
                applied = list(connection.execute(text("SELECT version_num FROM alembic_version")).scalars())
            ready = len(heads) == 1 and applied == heads
        except Exception:
            # Never expose connection strings or database exception arguments.
            pass
        response = jsonify(status="ok" if ready else "unavailable")
        response.headers["Cache-Control"] = "no-store"
        return response, 200 if ready else 503
