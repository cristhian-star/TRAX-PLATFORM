from datetime import datetime

from app import db


class BudgetRequest(db.Model):
    __tablename__ = "budget_requests"

    ESTADO_BORRADOR = "BORRADOR"
    ESTADO_PUBLICADA = "PUBLICADA"
    ESTADO_ABIERTO = "ABIERTO"
    ESTADO_COTIZANDO = "COTIZANDO"
    ESTADO_ADJUDICADA = "ADJUDICADA"
    ESTADO_CANCELADA = "CANCELADA"
    ESTADO_CERRADA = "CERRADA"

    ESTADOS = (
        ESTADO_BORRADOR,
        ESTADO_PUBLICADA,
        ESTADO_ABIERTO,
        ESTADO_COTIZANDO,
        ESTADO_ADJUDICADA,
        ESTADO_CANCELADA,
        ESTADO_CERRADA,
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    categoria = db.Column(db.String(120), nullable=False)
    titulo = db.Column(db.String(160), nullable=False)
    descripcion = db.Column(db.Text)
    zona = db.Column(db.String(120), nullable=False)
    fecha_estimada = db.Column(db.Date)
    urgencia = db.Column(db.String(50), nullable=False, default="NORMAL")
    estado = db.Column(db.String(50), nullable=False, default=ESTADO_PUBLICADA)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    offers = db.relationship(
        "BudgetOffer",
        back_populates="budget_request",
        cascade="all, delete-orphan",
        lazy="select",
    )
