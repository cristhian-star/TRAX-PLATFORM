"""Durable technical reconciliation; no commercial or accounting effects."""
from app import db


class PaymentOrderReconciliationWork(db.Model):
    __tablename__ = "payment_order_reconciliation_work"
    __table_args__ = (
        db.UniqueConstraint("event_id", name="uq_order_reconciliation_event"),
        db.CheckConstraint("attempt_count BETWEEN 0 AND 8", name="ck_order_work_attempts"),
        db.CheckConstraint("status IN ('QUEUED','PROCESSING','DONE','QUARANTINED','EXHAUSTED')", name="ck_order_work_status"),
        db.CheckConstraint("(status = 'PROCESSING' AND lease_token IS NOT NULL AND lease_until IS NOT NULL) OR (status <> 'PROCESSING' AND lease_token IS NULL AND lease_until IS NULL)", name="ck_order_work_lease"),
    )
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("psp_event_inbox.id", ondelete="RESTRICT"), nullable=False)
    status = db.Column(db.String(24), nullable=False)
    attempt_count = db.Column(db.Integer, nullable=False, default=0)
    next_attempt_at = db.Column(db.DateTime, nullable=False, index=True)
    lease_token = db.Column(db.String(36))
    lease_until = db.Column(db.DateTime)
    last_error = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, nullable=False)


class PaymentOrderReconciliationAttempt(db.Model):
    __tablename__ = "payment_order_reconciliation_attempts"
    __table_args__ = (
        db.UniqueConstraint("work_id", "number", name="uq_order_reconciliation_attempt"),
        db.CheckConstraint("number BETWEEN 1 AND 8", name="ck_order_attempt_number"),
        db.CheckConstraint("outcome IN ('STARTED','RECONCILED','RETRY','QUARANTINED','EXHAUSTED','LEASE_LOST')", name="ck_order_attempt_outcome"),
    )
    id = db.Column(db.Integer, primary_key=True)
    work_id = db.Column(db.Integer, db.ForeignKey("payment_order_reconciliation_work.id", ondelete="RESTRICT"), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    started_at = db.Column(db.DateTime, nullable=False)
    dispatched_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    outcome = db.Column(db.String(24), nullable=False)
    error_code = db.Column(db.String(32))


class PaymentOrderReconciliationEvidence(db.Model):
    __tablename__ = "payment_order_reconciliation_evidence"
    __table_args__ = (
        db.UniqueConstraint("payment_order_id", "snapshot_hash", name="uq_order_evidence_snapshot"),
        db.CheckConstraint("length(snapshot_hash) = 64", name="ck_order_evidence_hash"),
        db.CheckConstraint("timing IN ('BEFORE_LOCAL_EXPIRY','AFTER_LOCAL_EXPIRY','UNKNOWN')", name="ck_order_evidence_timing"),
    )
    id = db.Column(db.Integer, primary_key=True)
    payment_order_id = db.Column(db.Integer, db.ForeignKey("payment_orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("psp_event_inbox.id", ondelete="RESTRICT"), nullable=False)
    attempt_id = db.Column(db.Integer, db.ForeignKey("payment_order_reconciliation_attempts.id", ondelete="RESTRICT"), nullable=False)
    snapshot_hash = db.Column(db.String(64), nullable=False)
    remote_updated_at = db.Column(db.DateTime, nullable=False)
    observed_at = db.Column(db.DateTime, nullable=False)
    timing = db.Column(db.String(24), nullable=False)
    snapshot = db.Column(db.JSON, nullable=False)


class PaymentOrderReconciliationQuarantine(db.Model):
    __tablename__ = "payment_order_reconciliation_quarantine"
    __table_args__ = (
        db.UniqueConstraint("event_id", "content_hash", "reason", name="uq_order_quarantine_content"),
        db.CheckConstraint("length(content_hash) = 64", name="ck_order_quarantine_hash"),
    )
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("psp_event_inbox.id", ondelete="RESTRICT"), nullable=False)
    content_hash = db.Column(db.String(64), nullable=False)
    reason = db.Column(db.String(32), nullable=False)
    received_at = db.Column(db.DateTime, nullable=False)
