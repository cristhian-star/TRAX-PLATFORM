from datetime import datetime

from app import db


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    PLANES = (
        "FREE",
        "PRO",
        "ENTERPRISE",
    )

    ESTADOS = (
        "ACTIVA",
        "CANCELADA",
        "EXPIRADA",
        "PENDIENTE",
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan = db.Column(db.String(50), nullable=False, default="FREE")
    estado = db.Column(db.String(50), nullable=False, default="PENDIENTE")
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    auto_renew = db.Column(db.Boolean, nullable=False, default=False)
