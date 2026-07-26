from datetime import datetime

from app import db


class ContractRequest(db.Model):
    __tablename__ = "contract_requests"
    __table_args__ = (
        db.CheckConstraint(
            "source_type in ('DIRECT', 'BUDGET', 'PROPOSAL', 'EMERGENCY')",
            name="ck_contract_requests_source_type",
        ),
        db.CheckConstraint(
            "("
            "source_type = 'DIRECT' AND budget_offer_id IS NULL AND proposal_application_id IS NULL"
            ") OR ("
            "source_type = 'BUDGET' AND budget_offer_id IS NOT NULL AND proposal_application_id IS NULL AND source_id = budget_offer_id"
            ") OR ("
            "source_type = 'PROPOSAL' AND proposal_application_id IS NOT NULL AND budget_offer_id IS NULL AND source_id = proposal_application_id"
            ") OR ("
            "source_type = 'EMERGENCY' AND budget_offer_id IS NULL AND proposal_application_id IS NULL"
            ")",
            name="ck_contract_requests_source_consistency",
        ),
    )

    SOURCE_DIRECT = "DIRECT"
    SOURCE_BUDGET = "BUDGET"
    SOURCE_PROPOSAL = "PROPOSAL"
    SOURCE_EMERGENCY = "EMERGENCY"

    SOURCE_TYPES = (
        SOURCE_DIRECT,
        SOURCE_BUDGET,
        SOURCE_PROPOSAL,
        SOURCE_EMERGENCY,
    )

    ESTADOS = (
        "CREADA",
        "ACEPTADA",
        "RECHAZADA",
        "EN_PROGRESO",
        "COMPLETADA",
        "CONFIRMADA",
        "CANCELADA",
        "CERRADA",
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False)
    professional_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    source_type = db.Column(db.String(50), nullable=False, default=SOURCE_DIRECT, index=True)
    source_id = db.Column(db.Integer, index=True)
    budget_offer_id = db.Column(
        db.Integer,
        db.ForeignKey("budget_offers.id"),
        unique=True,
        nullable=True,
        index=True,
    )
    proposal_application_id = db.Column(
        db.Integer,
        db.ForeignKey("proposal_applications.id"),
        unique=True,
        nullable=True,
        index=True,
    )
    created_from_event = db.Column(db.String(80))
    servicio = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    precio_acordado = db.Column(db.Numeric(10, 2))
    estado = db.Column(db.String(50), nullable=False, default="CREADA")
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_inicio = db.Column(db.DateTime)
    fecha_fin = db.Column(db.DateTime)
    accepted_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    confirmed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)

    budget_offer = db.relationship("BudgetOffer", foreign_keys=[budget_offer_id])
    proposal_application = db.relationship("ProposalApplication", foreign_keys=[proposal_application_id])
    events = db.relationship(
        "ContractEvent",
        back_populates="contract",
        lazy="select",
        passive_deletes=True,
    )
