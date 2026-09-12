from app import db


class PSPEventRecord(db.Model):
    __tablename__ = "psp_event_inbox"
    __table_args__ = (
        db.UniqueConstraint(
            "provider", "test_mode", "external_event_id",
            name="uq_psp_event_inbox_identity",
        ),
        db.CheckConstraint("length(trim(provider)) > 0", name="ck_psp_event_inbox_provider_nonempty"),
        db.CheckConstraint("length(trim(external_event_id)) > 0", name="ck_psp_event_inbox_event_id_nonempty"),
        db.CheckConstraint("length(trim(topic)) > 0", name="ck_psp_event_inbox_topic_nonempty"),
        db.CheckConstraint("length(trim(action)) > 0", name="ck_psp_event_inbox_action_nonempty"),
        db.CheckConstraint("length(trim(external_resource_id)) > 0", name="ck_psp_event_inbox_resource_id_nonempty"),
        db.CheckConstraint("length(payload_hash) = 64", name="ck_psp_event_inbox_payload_hash_length"),
    )

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(64), nullable=False)
    external_event_id = db.Column(db.String(255), nullable=False)
    topic = db.Column(db.String(128), nullable=False)
    action = db.Column(db.String(128), nullable=False)
    external_resource_id = db.Column(db.String(255), nullable=False)
    test_mode = db.Column(db.Boolean, nullable=False)
    occurred_at = db.Column(db.DateTime(timezone=True), nullable=True)
    received_at = db.Column(db.DateTime(timezone=True), nullable=False)
    payload_hash = db.Column(db.String(64), nullable=False)
