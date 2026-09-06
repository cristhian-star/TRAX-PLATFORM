from datetime import datetime

from app import db


class VerificationRequest(db.Model):
    __tablename__ = "verification_requests"

    ESTADOS = (
        "PENDIENTE",
        "APROBADO",
        "OBSERVADO",
        "RECHAZADO",
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    tipo_usuario = db.Column(db.String(50), nullable=False)
    documento_identidad = db.Column(db.String(255))
    certificado_oficio = db.Column(db.String(255))
    titulo_profesional = db.Column(db.String(255))
    material_probatorio = db.Column(db.Text)
    estado = db.Column(db.String(50), nullable=False, default="PENDIENTE")
    observaciones = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
