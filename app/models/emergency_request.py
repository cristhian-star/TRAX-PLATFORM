from datetime import datetime

from app import db


class EmergencyRequest(db.Model):
    __tablename__ = "emergency_requests"

    ESTADOS = (
        "ABIERTA",
        "ASIGNADA",
        "EN_CAMINO",
        "RESUELTA",
        "CANCELADA",
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    categoria = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    zona = db.Column(db.String(120), nullable=False)
    prioridad = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.String(50), nullable=False, default="ABIERTA")
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
