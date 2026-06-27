from datetime import datetime

from app import db


class BudgetOffer(db.Model):
    __tablename__ = "budget_offers"
    __table_args__ = (
        db.UniqueConstraint(
            "budget_request_id",
            "professional_id",
            name="uq_budget_offer_request_professional",
        ),
    )

    ESTADOS = (
        "ENVIADO",
        "ADJUDICADO",
    )

    id = db.Column(db.Integer, primary_key=True)
    budget_request_id = db.Column(
        db.Integer,
        db.ForeignKey("budget_requests.id"),
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
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    cobra_visita = db.Column(db.Boolean, nullable=False, default=False)
    precio_visita = db.Column(db.Numeric(12, 2))
    monto_desde = db.Column(db.Numeric(12, 2))
    monto_hasta = db.Column(db.Numeric(12, 2))
    mensaje = db.Column(db.Text, nullable=False)
    plazo_estimado = db.Column(db.String(120), nullable=False)
    condiciones = db.Column(db.Text)
    estado = db.Column(db.String(50), nullable=False, default="ENVIADO")
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    budget_request = db.relationship("BudgetRequest", back_populates="offers")
    professional = db.relationship("Professional")
