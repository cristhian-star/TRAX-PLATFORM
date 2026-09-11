from datetime import datetime, timezone

from app import db


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PaymentAttemptRecord(db.Model):
    __tablename__ = "payment_attempts"
    __table_args__ = (
        db.UniqueConstraint("idempotency_key", name="uq_payment_attempts_idempotency_key"),
        db.CheckConstraint("length(trim(idempotency_key)) > 0", name="ck_payment_attempts_key_nonempty"),
        db.CheckConstraint(
            "financial_status IS NULL OR financial_status IN ('APPROVED','REJECTED','PENDING')",
            name="ck_payment_attempts_financial_status_valid",
        ),
        db.CheckConstraint(
            "orchestration_result IN ('APPROVED','REJECTED','PENDING','RECONCILIATION_REQUIRED')",
            name="ck_payment_attempts_result_valid",
        ),
        db.CheckConstraint(
            "(orchestration_result = 'RECONCILIATION_REQUIRED' AND requires_reconciliation = true AND financial_status IS NULL) OR "
            "(orchestration_result <> 'RECONCILIATION_REQUIRED' AND requires_reconciliation = false AND financial_status = orchestration_result)",
            name="ck_payment_attempts_result_coherent",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    obligation_id = db.Column(
        db.Integer,
        db.ForeignKey("payment_obligations.id", ondelete="RESTRICT", name="fk_payment_attempts_obligation"),
        nullable=False,
        index=True,
    )
    idempotency_key = db.Column(db.String(160), nullable=False)
    external_attempt_id = db.Column(db.String(255), nullable=True)
    financial_status = db.Column(db.String(32), nullable=True)
    orchestration_result = db.Column(db.String(32), nullable=False)
    requires_reconciliation = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    obligation = db.relationship("PaymentObligation", backref=db.backref("payment_attempts", lazy="select"))
