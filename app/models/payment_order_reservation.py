from app import db


class PaymentOrderReservation(db.Model):
    __tablename__ = "payment_order_reservations"
    __table_args__ = (
        db.UniqueConstraint("obligation_id", name="uq_payment_order_reservations_obligation"),
        db.UniqueConstraint("local_order_id", name="uq_payment_order_reservations_local_order"),
        db.UniqueConstraint("idempotency_key", name="uq_payment_order_reservations_idempotency"),
        db.UniqueConstraint("external_reference", name="uq_payment_order_reservations_external_reference"),
        db.UniqueConstraint("payment_order_id", name="uq_payment_order_reservations_order"),
        db.CheckConstraint(
            "status IN ('PREPARED','CALL_IN_PROGRESS','SUCCEEDED','UNCERTAIN')",
            name="ck_payment_order_reservations_status",
        ),
        db.CheckConstraint(
            "(status IN ('PREPARED','CALL_IN_PROGRESS') AND payment_order_id IS NULL AND finished_at IS NULL) OR "
            "(status = 'UNCERTAIN' AND payment_order_id IS NULL AND finished_at IS NOT NULL) OR "
            "(status = 'SUCCEEDED' AND payment_order_id IS NOT NULL AND finished_at IS NOT NULL)",
            name="ck_payment_order_reservations_completion",
        ),
        db.CheckConstraint(
            "amount > 0 AND amount < 1e62 AND amount = round(amount, 2)",
            name="ck_payment_order_reservations_amount",
        ),
        db.CheckConstraint("currency = 'ARS'", name="ck_payment_order_reservations_currency"),
        db.CheckConstraint(
            "expires_at = created_at + interval '72 hours'",
            name="ck_payment_order_reservations_expiry",
        ).ddl_if(dialect="postgresql"),
        db.CheckConstraint(
            "abs((julianday(expires_at) - julianday(created_at)) - 3.0) < 0.00000001",
            name="ck_payment_order_reservations_expiry",
        ).ddl_if(dialect="sqlite"),
    )

    id = db.Column(db.Integer, primary_key=True)
    obligation_id = db.Column(db.Integer, db.ForeignKey(
        "payment_obligations.id", ondelete="RESTRICT", name="fk_payment_order_reservations_obligation"
    ), nullable=False)
    actor_user_id = db.Column(db.Integer, db.ForeignKey(
        "users.id", ondelete="RESTRICT", name="fk_payment_order_reservations_actor"
    ), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey(
        "professionals.id", ondelete="RESTRICT", name="fk_payment_order_reservations_professional"
    ), nullable=False)
    payment_order_id = db.Column(db.Integer, db.ForeignKey(
        "payment_orders.id", ondelete="RESTRICT", name="fk_payment_order_reservations_order"
    ), nullable=True)
    local_order_id = db.Column(db.String(160), nullable=False)
    obligation_reference = db.Column(db.String(160), nullable=False)
    external_reference = db.Column(db.String(160), nullable=False)
    idempotency_key = db.Column(db.String(160), nullable=False)
    amount = db.Column(db.Numeric, nullable=False)
    currency = db.Column(db.String(16), nullable=False)
    concept = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(24), nullable=False, default="PREPARED")
    finished_at = db.Column(db.DateTime, nullable=True)
