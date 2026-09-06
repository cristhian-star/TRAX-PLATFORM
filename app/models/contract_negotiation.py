from datetime import datetime, timezone

from app import db


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ContractNegotiation(db.Model):
    __tablename__ = "contract_negotiations"
    __table_args__ = (
        db.CheckConstraint(
            "state in ('OPEN', 'AGREED', 'CANCELLED', 'REJECTED', 'CONTRACTED')",
            name="ck_contract_negotiations_state",
        ),
        db.CheckConstraint(
            "contracting_mode = 'EXTERNAL'",
            name="ck_contract_negotiations_contracting_mode",
        ),
        db.CheckConstraint(
            "version >= 1 AND current_terms_version >= 1",
            name="ck_contract_negotiations_versions",
        ),
        db.CheckConstraint(
            "agreed_terms_version IS NULL OR agreed_terms_version >= 1",
            name="ck_contract_negotiations_agreed_version",
        ),
        db.CheckConstraint(
            "agreed_terms_version IS NULL "
            "OR agreed_terms_version = current_terms_version",
            name="ck_contract_negotiations_agreed_is_current",
        ),
        db.CheckConstraint(
            "state NOT IN ('AGREED', 'CONTRACTED') "
            "OR agreed_terms_version IS NOT NULL",
            name="ck_contract_negotiations_agreed_state",
        ),
        db.CheckConstraint(
            "(state = 'CONTRACTED' AND contract_id IS NOT NULL) "
            "OR (state <> 'CONTRACTED' AND contract_id IS NULL)",
            name="ck_contract_negotiations_contract_state",
        ),
        db.CheckConstraint(
            "cliente_id <> professional_user_id",
            name="ck_contract_negotiations_distinct_parties",
        ),
    )

    STATE_OPEN = "OPEN"
    STATE_AGREED = "AGREED"
    STATE_CANCELLED = "CANCELLED"
    STATE_REJECTED = "REJECTED"
    STATE_CONTRACTED = "CONTRACTED"
    STATES = (
        STATE_OPEN,
        STATE_AGREED,
        STATE_CANCELLED,
        STATE_REJECTED,
        STATE_CONTRACTED,
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    professional_id = db.Column(
        db.Integer,
        db.ForeignKey("professionals.id"),
        nullable=False,
        index=True,
    )
    professional_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    servicio = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(20), nullable=False, default=STATE_OPEN)
    contracting_mode = db.Column(
        db.String(20),
        nullable=False,
        default="EXTERNAL",
        server_default="EXTERNAL",
    )
    version = db.Column(db.Integer, nullable=False, default=1, server_default="1")
    current_terms_version = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    agreed_terms_version = db.Column(db.Integer)
    contract_id = db.Column(
        db.Integer,
        db.ForeignKey("contract_requests.id", ondelete="RESTRICT"),
        unique=True,
        index=True,
    )
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    client = db.relationship("User", foreign_keys=[cliente_id])
    professional_user = db.relationship("User", foreign_keys=[professional_user_id])
    professional = db.relationship("Professional")
    contract = db.relationship("ContractRequest", foreign_keys=[contract_id])
    terms_versions = db.relationship(
        "ContractNegotiationVersion",
        back_populates="negotiation",
        order_by="ContractNegotiationVersion.version_no",
        passive_deletes=True,
    )
    acceptances = db.relationship(
        "NegotiationAcceptance",
        back_populates="negotiation",
        passive_deletes=True,
    )
    events = db.relationship(
        "NegotiationEvent",
        back_populates="negotiation",
        order_by="NegotiationEvent.sequence_no",
        passive_deletes=True,
    )
