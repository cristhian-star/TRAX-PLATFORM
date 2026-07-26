from datetime import datetime

from app import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    entity_type = db.Column(db.String(80), index=True)
    entity_id = db.Column(db.Integer, index=True)
    contract_id = db.Column(db.Integer, db.ForeignKey("contract_requests.id"), index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("contract_events.id"), index=True)
    idempotency_key = db.Column(db.String(160), index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
