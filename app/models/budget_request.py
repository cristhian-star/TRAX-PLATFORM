from datetime import datetime

from app import db


class BudgetRequest(db.Model):
    __tablename__ = "budget_requests"

    ESTADOS = (
        "ABIERTO",
        "COTIZANDO",
        "CERRADO",
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    categoria = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    zona = db.Column(db.String(120), nullable=False)
    estado = db.Column(db.String(50), nullable=False, default="ABIERTO")
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
