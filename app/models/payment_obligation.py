from datetime import datetime, timezone

from app import db


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PaymentObligation(db.Model):
    __tablename__ = "payment_obligations"
    __table_args__ = (
        db.UniqueConstraint("internal_reference", name="uq_payment_obligations_reference"),
        db.CheckConstraint("amount > 0", name="ck_payment_obligations_amount_positive"),
        db.CheckConstraint("length(trim(internal_reference)) > 0", name="ck_payment_obligations_reference_nonempty"),
        db.CheckConstraint("length(trim(currency)) > 0", name="ck_payment_obligations_currency_nonempty"),
    )

    id = db.Column(db.Integer, primary_key=True)
    internal_reference = db.Column(db.String(160), nullable=False)
    amount = db.Column(db.Numeric, nullable=False)
    currency = db.Column(db.String(16), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
