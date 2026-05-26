from datetime import datetime

from app import db


class ContractRequest(db.Model):
    __tablename__ = "contract_requests"

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
