from datetime import datetime

from app import db


class AbuseReport(db.Model):
    __tablename__ = "abuse_reports"

    ESTADOS = (
        "ABIERTO",
        "EN_REVISION",
        "RESUELTO",
        "DESCARTADO",
    )

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    motivo = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(50), nullable=False, default="ABIERTO")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"))
