from app import db
from app.services.pro_time import as_utc_naive, utc_now


class Subscription(db.Model):
    __tablename__ = "subscriptions"
    __table_args__ = (
        db.CheckConstraint(
            "source_type IS NULL OR source_type IN ('TRANSACTIONAL', 'SUBSCRIPTION')",
            name="ck_subscriptions_source_type_valid",
        ),
    )

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

    SOURCE_TYPES = (
        "TRANSACTIONAL",
        "SUBSCRIPTION",
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan = db.Column(db.String(50), nullable=False, default="FREE")
    estado = db.Column(db.String(50), nullable=False, default="PENDIENTE")
    source_type = db.Column(db.String(50), nullable=True)
    started_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: as_utc_naive(utc_now()),
    )
    expires_at = db.Column(db.DateTime)
    auto_renew = db.Column(db.Boolean, nullable=False, default=False)
