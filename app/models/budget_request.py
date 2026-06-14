from datetime import datetime

from app import db


class BudgetRequest(db.Model):
    __tablename__ = "budget_requests"

    ESTADOS = (
        "ABIERTO",
        "COTIZANDO",
        "ADJUDICADA",
        "CERRADO",
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    categoria = db.Column(db.String(120), nullable=False)
    titulo = db.Column(db.String(160), nullable=False)
    descripcion = db.Column(db.Text)
    zona = db.Column(db.String(120), nullable=False)
    fecha_estimada = db.Column(db.Date)
    urgencia = db.Column(db.String(50), nullable=False, default="NORMAL")
    estado = db.Column(db.String(50), nullable=False, default="ABIERTO")
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    offers = db.relationship(
        "BudgetOffer",
        back_populates="budget_request",
        cascade="all, delete-orphan",
        lazy="select",
    )
