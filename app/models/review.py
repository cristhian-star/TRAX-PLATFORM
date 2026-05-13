from datetime import datetime

from app import db


class Review(db.Model):
    __tablename__ = "reviews"

    ESTADOS = (
        "VISIBLE",
        "OCULTA",
        "REPORTADA",
    )

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comentario = db.Column(db.Text)
    estado = db.Column(db.String(50), nullable=False, default="VISIBLE")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
