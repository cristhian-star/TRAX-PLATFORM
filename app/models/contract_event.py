from datetime import datetime

from app import db


class ContractEvent(db.Model):
    __tablename__ = "contract_events"

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
    previous_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50))
    metadata_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    contract = db.relationship("ContractRequest", back_populates="events")
    actor_user = db.relationship("User")
