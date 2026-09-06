from datetime import datetime, timezone

from sqlalchemy import event, select

from app import db


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class NegotiationAcceptance(db.Model):
    __tablename__ = "negotiation_acceptances"
    __table_args__ = (
        db.UniqueConstraint(
            "negotiation_version_id",
            "party",
            name="uq_negotiation_acceptances_version_party",
        ),
        db.ForeignKeyConstraint(
            ["negotiation_version_id", "negotiation_id"],
            [
                "contract_negotiation_versions.id",
                "contract_negotiation_versions.negotiation_id",
            ],
            name="fk_negotiation_acceptances_version_negotiation",
            ondelete="RESTRICT",
        ),
        db.CheckConstraint(
            "party in ('CLIENT', 'PROFESSIONAL')",
            name="ck_negotiation_acceptances_party",
        ),
    )

    PARTY_CLIENT = "CLIENT"
    PARTY_PROFESSIONAL = "PROFESSIONAL"
    PARTIES = (PARTY_CLIENT, PARTY_PROFESSIONAL)

    id = db.Column(db.Integer, primary_key=True)
    negotiation_id = db.Column(
        db.Integer,
        db.ForeignKey("contract_negotiations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    negotiation_version_id = db.Column(
        db.Integer,
        db.ForeignKey("contract_negotiation_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    party = db.Column(db.String(20), nullable=False)
    accepted_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    negotiation = db.relationship(
        "ContractNegotiation",
        back_populates="acceptances",
    )
    negotiation_version = db.relationship(
        "ContractNegotiationVersion",
        foreign_keys=[negotiation_version_id],
        overlaps="acceptances,negotiation",
    )
    actor_user = db.relationship("User")


def _validate_acceptance_before_write(_mapper, connection, target):
    from app.models.contract_negotiation import ContractNegotiation
    from app.models.contract_negotiation_version import (
        ContractNegotiationVersion,
    )
    from app.models.user import User

    negotiation = connection.execute(
        select(
            ContractNegotiation.cliente_id,
            ContractNegotiation.professional_user_id,
            ContractNegotiation.current_terms_version,
        ).where(ContractNegotiation.id == target.negotiation_id)
    ).one_or_none()
    version = connection.execute(
        select(
            ContractNegotiationVersion.negotiation_id,
            ContractNegotiationVersion.version_no,
        ).where(
            ContractNegotiationVersion.id
            == target.negotiation_version_id
        )
    ).one_or_none()
    actor = connection.execute(
        select(User.rol, User.estado).where(
            User.id == target.actor_user_id
        )
    ).one_or_none()
    if negotiation is None or version is None or actor is None:
        raise ValueError("La aceptacion referencia entidades inexistentes")
    if (
        version.negotiation_id != target.negotiation_id
        or version.version_no != negotiation.current_terms_version
    ):
        raise ValueError("La aceptacion debe corresponder a la version vigente")
    if target.party == NegotiationAcceptance.PARTY_CLIENT:
        valid_identity = (
            target.actor_user_id == negotiation.cliente_id
            and actor.rol == "CLIENTE"
        )
    elif target.party == NegotiationAcceptance.PARTY_PROFESSIONAL:
        valid_identity = (
            target.actor_user_id == negotiation.professional_user_id
            and actor.rol == "PROFESIONAL"
        )
    else:
        valid_identity = False
    if not valid_identity or actor.estado != "ACTIVO":
        raise ValueError("La identidad de la aceptacion es incoherente")


event.listen(
    NegotiationAcceptance,
    "before_insert",
    _validate_acceptance_before_write,
    propagate=True,
)
event.listen(
    NegotiationAcceptance,
    "before_update",
    _validate_acceptance_before_write,
    propagate=True,
)
