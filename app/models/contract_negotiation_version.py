from datetime import datetime, timezone

from sqlalchemy import event, inspect

from app import db


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ContractNegotiationVersion(db.Model):
    __tablename__ = "contract_negotiation_versions"
    __table_args__ = (
        db.UniqueConstraint(
            "negotiation_id",
            "version_no",
            name="uq_contract_negotiation_versions_number",
        ),
        db.UniqueConstraint(
            "id",
            "negotiation_id",
            name="uq_contract_negotiation_versions_id_negotiation",
        ),
        db.CheckConstraint(
            "version_no >= 1",
            name="ck_contract_negotiation_versions_number",
        ),
        db.CheckConstraint(
            "external_price >= 0",
            name="ck_contract_negotiation_versions_price",
        ),
        db.CheckConstraint(
            "estimated_start_at IS NULL OR estimated_end_at IS NULL "
            "OR estimated_start_at <= estimated_end_at",
            name="ck_contract_negotiation_versions_dates",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    negotiation_id = db.Column(
        db.Integer,
        db.ForeignKey("contract_negotiations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    version_no = db.Column(db.Integer, nullable=False)
    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    description = db.Column(db.Text, nullable=False)
    scope = db.Column(db.Text, nullable=False)
    external_price = db.Column(db.Numeric(10, 2), nullable=False)
    estimated_start_at = db.Column(db.DateTime)
    estimated_end_at = db.Column(db.DateTime)
    observations = db.Column(db.Text)
    payload_hash = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    negotiation = db.relationship(
        "ContractNegotiation",
        back_populates="terms_versions",
    )
    actor_user = db.relationship("User")


@event.listens_for(ContractNegotiationVersion, "before_update", propagate=True)
def _prevent_contract_negotiation_version_update(_mapper, _connection, target):
    state = inspect(target)
    if any(
        attribute.history.has_changes()
        for attribute in state.attrs
        if attribute.key in target.__table__.columns
    ):
        raise ValueError(
            "ContractNegotiationVersion es inmutable; cree una nueva version"
        )
