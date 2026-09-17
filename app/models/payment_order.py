from datetime import datetime, timezone

from app import db


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PaymentOrder(db.Model):
    __tablename__ = "payment_orders"
    __table_args__ = (
        db.UniqueConstraint("local_order_id", name="uq_payment_orders_local_order_id"),
        db.UniqueConstraint("idempotency_key", name="uq_payment_orders_idempotency_key"),
        db.UniqueConstraint("external_reference", name="uq_payment_orders_external_reference"),
        db.UniqueConstraint(
            "provider", "live_mode", "external_order_id",
            name="uq_payment_orders_psp_identity",
        ),
        db.CheckConstraint(
            "amount > 0 AND amount < 1e62 AND amount = round(amount, 2)",
            name="ck_payment_orders_amount_valid",
        ),
        db.CheckConstraint("currency = 'ARS'", name="ck_payment_orders_currency_ars"),
        db.CheckConstraint(
            "status IN ('ACTIVE','EXPIRED','CANCELLED')",
            name="ck_payment_orders_status_valid",
        ),
        db.CheckConstraint(
            "expires_at = created_at + interval '72 hours'",
            name="ck_payment_orders_expiry_72h",
        ).ddl_if(dialect="postgresql"),
        db.CheckConstraint(
            "abs((julianday(expires_at) - julianday(created_at)) - 3.0) "
            "< 0.00000001",
            name="ck_payment_orders_expiry_72h",
        ).ddl_if(dialect="sqlite"),
        db.CheckConstraint(
            "(status = 'ACTIVE' AND closed_at IS NULL AND cancelled_at IS NULL) OR "
            "(status = 'EXPIRED' AND closed_at IS NOT NULL AND "
            "closed_at = expires_at AND cancelled_at IS NULL) OR "
            "(status = 'CANCELLED' AND closed_at IS NOT NULL AND "
            "cancelled_at IS NOT NULL AND closed_at = cancelled_at AND "
            "cancelled_at >= created_at AND cancelled_at < expires_at)",
            name="ck_payment_orders_status_timestamps_coherent",
        ),
        db.Index(
            "uq_payment_orders_active_obligation",
            "obligation_id",
            unique=True,
            postgresql_where=db.text("status = 'ACTIVE'"),
            sqlite_where=db.text("status = 'ACTIVE'"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    obligation_id = db.Column(
        db.Integer,
        db.ForeignKey("payment_obligations.id", ondelete="RESTRICT", name="fk_payment_orders_obligation"),
        nullable=False,
        index=True,
    )
    professional_id = db.Column(
        db.Integer,
        db.ForeignKey("professionals.id", ondelete="RESTRICT", name="fk_payment_orders_professional"),
        nullable=False,
        index=True,
    )
    local_order_id = db.Column(db.String(160), nullable=False)
    external_reference = db.Column(db.String(160), nullable=False)
    idempotency_key = db.Column(db.String(160), nullable=False)
    amount = db.Column(db.Numeric, nullable=False)
    currency = db.Column(db.String(16), nullable=False)
    concept = db.Column(db.String(200), nullable=False)
    provider = db.Column(db.String(64), nullable=False)
    live_mode = db.Column(db.Boolean, nullable=False)
    external_order_id = db.Column(db.String(160), nullable=False)
    checkout_url = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(16), nullable=False, default="ACTIVE")
    created_at = db.Column(db.DateTime, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    closed_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    obligation = db.relationship("PaymentObligation", backref=db.backref("payment_orders", lazy="select"))
    professional = db.relationship("Professional", backref=db.backref("payment_orders", lazy="select"))
