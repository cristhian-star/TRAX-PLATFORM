from app import db


class ActivityNotification(db.Model):
    __tablename__ = "activity_notifications"
    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "contract_event_id",
            "template_key",
            "channel",
            name="uq_activity_notifications_domain_delivery",
        ),
        db.UniqueConstraint(
            "user_id",
            "negotiation_event_id",
            "template_key",
            "channel",
            name="uq_activity_notifications_negotiation_delivery",
        ),
        db.CheckConstraint(
            "channel in ('INTERNAL')",
            name="ck_activity_notifications_channel",
        ),
        db.CheckConstraint(
            "delivery_status in ('PENDING', 'DELIVERED', 'FAILED')",
            name="ck_activity_notifications_delivery_status",
        ),
        db.CheckConstraint(
            "attempt_count >= 0",
            name="ck_activity_notifications_attempt_count",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    contract_event_id = db.Column(
        db.Integer,
        db.ForeignKey("contract_events.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    negotiation_event_id = db.Column(
        db.Integer,
        db.ForeignKey("negotiation_events.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    correlation_id = db.Column(db.String(36), nullable=True, index=True)
    idempotency_key = db.Column(db.String(160), nullable=True, unique=True)
    template_key = db.Column(db.String(80), nullable=True)
    channel = db.Column(db.String(20), nullable=False, default="INTERNAL", server_default="INTERNAL")
    delivery_status = db.Column(
        db.String(20),
        nullable=False,
        default="DELIVERED",
        server_default="DELIVERED",
    )
    attempt_count = db.Column(db.Integer, nullable=False, default=0, server_default="0")
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
    contract_event = db.relationship("ContractEvent")
    negotiation_event = db.relationship("NegotiationEvent")

    @property
    def recipient_user_id(self):
        """Canonical domain name; user_id remains the compatible database column."""
        return self.user_id
