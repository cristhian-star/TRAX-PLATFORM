from datetime import datetime, timezone

from app import db


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class OperationCommand(db.Model):
    __tablename__ = "operation_commands"
    __table_args__ = (
        db.UniqueConstraint(
            "actor_user_id",
            "operation",
            "idempotency_key",
            name="uq_operation_commands_actor_operation_key",
        ),
        db.CheckConstraint(
            "status in ('PROCESSING', 'SUCCEEDED', 'FAILED')",
            name="ck_operation_commands_status",
        ),
    )

    STATUS_PROCESSING = "PROCESSING"
    STATUS_SUCCEEDED = "SUCCEEDED"
    STATUS_FAILED = "FAILED"
    STATUSES = (STATUS_PROCESSING, STATUS_SUCCEEDED, STATUS_FAILED)

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    operation = db.Column(db.String(80), nullable=False)
    idempotency_key = db.Column(db.String(160), nullable=False)
    payload_hash = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_PROCESSING)
    result_entity_type = db.Column(db.String(80))
    result_entity_id = db.Column(db.Integer)
    correlation_id = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    completed_at = db.Column(db.DateTime)
    failure_code = db.Column(db.String(80))

    actor_user = db.relationship("User")
