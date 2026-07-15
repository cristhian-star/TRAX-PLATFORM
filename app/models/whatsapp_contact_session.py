from app import db


class WhatsAppContactSession(db.Model):
    __tablename__ = "whatsapp_contact_sessions"

    STATUS_INICIADA = "INICIADA"
    STATUS_CONTACTO_ABIERTO = "CONTACTO_ABIERTO"
    STATUS_FINALIZADA = "FINALIZADA"
    STATUS_CANCELADA = "CANCELADA"

    STATUSES = (
        STATUS_INICIADA,
        STATUS_CONTACTO_ABIERTO,
        STATUS_FINALIZADA,
        STATUS_CANCELADA,
    )

    id = db.Column(db.Integer, primary_key=True)
    client_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False, index=True)
    operation_type = db.Column(db.String(80), nullable=False, index=True)
    entity_type = db.Column(db.String(80), nullable=True, index=True)
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    status = db.Column(db.String(50), nullable=False, default=STATUS_INICIADA, index=True)
    contact_identifier_type = db.Column(db.String(20), nullable=True)
    contact_identifier_masked = db.Column(db.String(120), nullable=True)
    consent_given = db.Column(db.Boolean, nullable=False, default=False)
    consent_at = db.Column(db.DateTime, nullable=True)
    initiated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), index=True)
    last_status_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    metadata_json = db.Column(db.JSON, nullable=True)

    client_user = db.relationship("User", foreign_keys=[client_user_id])
    professional = db.relationship("Professional")
