from datetime import datetime

from app import db


class ReputationEvent(db.Model):
    __tablename__ = "reputation_events"

    TIPOS_EVENTO = (
        "TRABAJO_COMPLETADO",
        "REVIEW_POSITIVA",
        "REVIEW_NEGATIVA",
        "REPORTE_ABUSO",
        "VERIFICACION_APROBADA",
        "VERIFICACION_RECHAZADA",
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    tipo_evento = db.Column(db.String(80), nullable=False)
    puntos = db.Column(db.Integer, nullable=False, default=0)
    descripcion = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
