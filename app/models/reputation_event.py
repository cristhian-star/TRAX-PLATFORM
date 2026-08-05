from datetime import datetime

from app import db


class ReputationEvent(db.Model):
    __tablename__ = "reputation_events"
    __table_args__ = (
        db.CheckConstraint(
            "source_type IS NULL OR source_type IN "
            "('CONTRACT_REVIEW', 'LEGACY_EVENT')",
            name="ck_reputation_events_source_type",
        ),
        db.CheckConstraint(
            "origin IS NULL OR origin IN ('CONTRACTUAL', 'LEGACY')",
            name="ck_reputation_events_origin",
        ),
        db.CheckConstraint(
            "source_type IS NOT NULL AND origin IS NOT NULL",
            name="ck_reputation_events_discriminators_required_v2",
        ),
        db.CheckConstraint(
            "source_type <> 'CONTRACT_REVIEW' OR ("
            "review_id IS NOT NULL AND contract_id IS NOT NULL "
            "AND user_id IS NOT NULL AND correlation_id IS NOT NULL "
            "AND event_type = 'REVIEW_RECORDED' "
            "AND event_value BETWEEN 1 AND 5 "
            "AND origin = 'CONTRACTUAL' AND puntos IS NULL)",
            name="ck_reputation_events_contract_review_integrity",
        ),
    )

    TIPOS_EVENTO = (
        "TRABAJO_COMPLETADO",
        "REVIEW_POSITIVA",
        "REVIEW_NEGATIVA",
        "REPORTE_ABUSO",
        "VERIFICACION_APROBADA",
        "VERIFICACION_RECHAZADA",
    )

    SOURCE_CONTRACT_REVIEW = "CONTRACT_REVIEW"
    SOURCE_LEGACY_EVENT = "LEGACY_EVENT"
    SOURCE_TYPES = (SOURCE_CONTRACT_REVIEW, SOURCE_LEGACY_EVENT)

    EVENT_REVIEW_RECORDED = "REVIEW_RECORDED"
    EVENT_TYPES = (EVENT_REVIEW_RECORDED,)

    ORIGIN_CONTRACTUAL = "CONTRACTUAL"
    ORIGIN_LEGACY = "LEGACY"
    ORIGINS = (ORIGIN_CONTRACTUAL, ORIGIN_LEGACY)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    review_id = db.Column(
        db.Integer,
        db.ForeignKey("reviews.id"),
        nullable=True,
        unique=True,
        index=True,
    )
    contract_id = db.Column(
        db.Integer,
        db.ForeignKey("contract_requests.id"),
        nullable=True,
        index=True,
    )
    source_type = db.Column(db.String(30), nullable=True)
    event_type = db.Column(db.String(50), nullable=True)
    event_value = db.Column(db.Integer, nullable=True)
    origin = db.Column(db.String(20), nullable=True)
    correlation_id = db.Column(db.String(36), nullable=True, index=True)
    tipo_evento = db.Column(db.String(80), nullable=False)
    puntos = db.Column(db.Integer, nullable=True)
    descripcion = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    review = db.relationship("Review")
    contract = db.relationship("ContractRequest")
