from app import db


class ActivityNotification(db.Model):
    __tablename__ = "activity_notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    tipo = db.Column(db.String(80), nullable=False, index=True)
    categoria = db.Column(db.String(50), nullable=False, index=True)
    titulo = db.Column(db.String(180), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    url_destino = db.Column(db.String(255), nullable=True)
    entity_type = db.Column(db.String(80), nullable=True, index=True)
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    prioridad = db.Column(db.String(50), nullable=False, default="INFO", index=True)
    requiere_accion = db.Column(db.Boolean, nullable=False, default=False)
    leida = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), index=True)
    read_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], backref="activity_notifications")
    actor_user = db.relationship("User", foreign_keys=[actor_user_id])
