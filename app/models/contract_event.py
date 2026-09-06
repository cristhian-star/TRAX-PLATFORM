from datetime import datetime

from app import db


class ContractEvent(db.Model):
    __tablename__ = "contract_events"
    __table_args__ = (
        db.UniqueConstraint(
            "contract_id",
            "sequence_no",
            name="uq_contract_events_contract_sequence",
        ),
        db.UniqueConstraint(
            "idempotency_key",
            name="uq_contract_events_idempotency_key",
        ),
        db.CheckConstraint(
            "sequence_no IS NULL OR sequence_no >= 1",
            name="ck_contract_events_sequence_positive",
        ),
    )

    CONTRACT_CREATED = "CONTRACT_CREATED"
    CONTRACT_ACCEPTED = "CONTRACT_ACCEPTED"
    CONTRACT_REJECTED = "CONTRACT_REJECTED"
    CONTRACT_STARTED = "CONTRACT_STARTED"
    CONTRACT_COMPLETED = "CONTRACT_COMPLETED"
    CONTRACT_CONFIRMED = "CONTRACT_CONFIRMED"
    CONTRACT_CANCELLED = "CONTRACT_CANCELLED"
    CREATED_FROM_BUDGET = "CREATED_FROM_BUDGET"
    CREATED_FROM_PROPOSAL = "CREATED_FROM_PROPOSAL"

    EVENT_TYPES = (
        CONTRACT_CREATED,
        CONTRACT_ACCEPTED,
        CONTRACT_REJECTED,
        CONTRACT_STARTED,
        CONTRACT_COMPLETED,
        CONTRACT_CONFIRMED,
        CONTRACT_CANCELLED,
        CREATED_FROM_BUDGET,
        CREATED_FROM_PROPOSAL,
    )

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(
        db.Integer,
        db.ForeignKey("contract_requests.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    event_type = db.Column(db.String(80), nullable=False, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    sequence_no = db.Column(db.Integer, nullable=False)
    correlation_id = db.Column(db.String(36), nullable=True, index=True)
    causation_event_id = db.Column(
        db.Integer,
        db.ForeignKey("contract_events.id", ondelete="RESTRICT"),
        nullable=True,
    )
    idempotency_key = db.Column(db.String(160), nullable=True)
    previous_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50))
    metadata_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    contract = db.relationship("ContractRequest", back_populates="events")
    actor_user = db.relationship("User")
    causation_event = db.relationship("ContractEvent", remote_side=[id])
