from datetime import datetime, timezone

from app import db


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class NegotiationEvent(db.Model):
    __tablename__ = "negotiation_events"
    __table_args__ = (
        db.UniqueConstraint(
            "negotiation_id",
            "sequence_no",
            name="uq_negotiation_events_sequence",
        ),
        db.UniqueConstraint(
            "negotiation_id",
            "idempotency_key",
            name="uq_negotiation_events_idempotency",
        ),
        db.CheckConstraint(
            "event_type in ('CREATED', 'TERMS_PROPOSED', 'TERMS_ACCEPTED', "
            "'AGREED', 'CANCELLED', 'REJECTED', 'CONTRACT_CREATED')",
            name="ck_negotiation_events_type",
        ),
        db.CheckConstraint(
            "sequence_no >= 1",
            name="ck_negotiation_events_sequence",
        ),
    )

    CREATED = "CREATED"
    TERMS_PROPOSED = "TERMS_PROPOSED"
    TERMS_ACCEPTED = "TERMS_ACCEPTED"
    AGREED = "AGREED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    CONTRACT_CREATED = "CONTRACT_CREATED"

    id = db.Column(db.Integer, primary_key=True)
    negotiation_id = db.Column(
        db.Integer,
        db.ForeignKey("contract_negotiations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    event_type = db.Column(db.String(40), nullable=False)
    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    sequence_no = db.Column(db.Integer, nullable=False)
    terms_version = db.Column(db.Integer)
    correlation_id = db.Column(db.String(36), nullable=False, index=True)
    idempotency_key = db.Column(db.String(160), nullable=False)
    metadata_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    negotiation = db.relationship(
        "ContractNegotiation",
        back_populates="events",
    )
    actor_user = db.relationship("User")
