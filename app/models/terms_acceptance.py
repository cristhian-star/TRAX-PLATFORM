from datetime import datetime

from app import db


class TermsAcceptance(db.Model):
    __tablename__ = "terms_acceptances"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    tipo_termino = db.Column(db.String(120), nullable=False)
    version = db.Column(db.String(50), nullable=False)
    accepted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
