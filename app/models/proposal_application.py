from datetime import datetime

from app import db


class ProposalApplication(db.Model):
    __tablename__ = "proposal_applications"

    ESTADOS = (
        "POSTULADA",
        "ACEPTADA",
        "RECHAZADA",
        "DESCARTADA",
    )

    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey("proposal_requests.id"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False)
    professional_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    experiencia_relevante = db.Column(db.Text)
    disponibilidad = db.Column(db.String(160))
    pretension_economica = db.Column(db.Numeric(12, 2))
    estado = db.Column(db.String(50), nullable=False, default="POSTULADA")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    proposal = db.relationship("ProposalRequest", back_populates="applications")
    professional = db.relationship("Professional")
    professional_user = db.relationship("User")
