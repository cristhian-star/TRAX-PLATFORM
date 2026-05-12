from datetime import datetime

from app import db


class ContractRequest(db.Model):
    __tablename__ = "contract_requests"

    ESTADOS = (
        "PENDIENTE",
        "ACEPTADO",
        "EN_PROCESO",
        "FINALIZADO",
        "CANCELADO",
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False)
    servicio = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    precio_acordado = db.Column(db.Numeric(10, 2))
    estado = db.Column(db.String(50), nullable=False, default="PENDIENTE")
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_inicio = db.Column(db.DateTime)
    fecha_fin = db.Column(db.DateTime)
