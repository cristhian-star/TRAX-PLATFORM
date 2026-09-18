"""Internal credit ledger; deliberately separate from accounting and PSP facts."""
from app import db
from decimal import Decimal
from sqlalchemy.types import TypeDecorator


class ExactCreditAmount(TypeDecorator):
    """SQLite must not round cents through a binary floating-point binding."""
    impl = db.Numeric(64, 2)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(db.String(66) if dialect.name == "sqlite" else db.Numeric(64, 2))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if type(value) is not Decimal or not value.is_finite() or value.as_tuple().exponent < -2:
            raise ValueError("invalid exact credit amount")
        return format(value, "f") if dialect.name == "sqlite" else value

    def process_result_value(self, value, dialect):
        return None if value is None else Decimal(value)


class TransactionalCreditPolicy(db.Model):
    __tablename__ = "transactional_credit_policies"
    version = db.Column(db.String(80), primary_key=True)
    currency = db.Column(db.String(3), nullable=False)
    threshold = db.Column(ExactCreditAmount(), nullable=False)
    __table_args__ = (
        db.CheckConstraint("currency = 'ARS'", name="ck_credit_policy_currency"),
        db.CheckConstraint("CAST(threshold AS NUMERIC) > 0 AND CAST(threshold AS NUMERIC) < 1e62 AND CAST(threshold AS NUMERIC) = round(CAST(threshold AS NUMERIC),2)", name="ck_credit_policy_threshold"),
    )


class PaymentEffectDecision(db.Model):
    __tablename__ = "payment_effect_decisions"
    id = db.Column(db.Integer, primary_key=True)
    evidence_id = db.Column(db.Integer, db.ForeignKey("payment_order_reconciliation_evidence.id", ondelete="RESTRICT"), nullable=False)
    status = db.Column(db.String(24), nullable=False)
    reason = db.Column(db.String(40), nullable=False)
    observed_at = db.Column(db.DateTime, nullable=False)
    __table_args__ = (
        db.UniqueConstraint("evidence_id", name="uq_payment_effect_evidence"),
        db.CheckConstraint("status IN ('PENDING_POLICY','PENDING_REVIEW','NOT_ELIGIBLE','ACCRUED','REPLAY','EXEMPT')", name="ck_effect_decision_status"),
    )


class TransactionalCommission(db.Model):
    __tablename__ = "transactional_commissions"
    id = db.Column(db.Integer, primary_key=True)
    payment_order_id = db.Column(db.Integer, db.ForeignKey("payment_orders.id", ondelete="RESTRICT"), nullable=False)
    evidence_id = db.Column(db.Integer, db.ForeignKey("payment_order_reconciliation_evidence.id", ondelete="RESTRICT"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id", ondelete="RESTRICT"), nullable=False)
    status = db.Column(db.String(24), nullable=False)
    policy_version = db.Column(db.String(80), db.ForeignKey("transactional_credit_policies.version", ondelete="RESTRICT"))
    provider = db.Column(db.String(32), nullable=False)
    live_mode = db.Column(db.Boolean, nullable=False)
    external_identity = db.Column(db.String(160))
    net_amount = db.Column(ExactCreditAmount())
    currency = db.Column(db.String(3))
    effective_at = db.Column(db.DateTime)
    paid_at = db.Column(db.DateTime)
    __table_args__ = (
        db.UniqueConstraint("payment_order_id", name="uq_commission_order"),
        db.UniqueConstraint("provider", "live_mode", "external_identity", name="uq_commission_financial_identity"),
        db.CheckConstraint("status IN ('PENDING_POLICY','PENDING_REVIEW','EFFECTIVE','EXEMPT')", name="ck_commission_status"),
        db.CheckConstraint("(status = 'EFFECTIVE' AND net_amount IS NOT NULL AND CAST(net_amount AS NUMERIC) > 0 AND currency = 'ARS' AND policy_version IS NOT NULL AND external_identity IS NOT NULL AND effective_at IS NOT NULL AND paid_at IS NOT NULL) OR (status <> 'EFFECTIVE' AND net_amount IS NULL)", name="ck_commission_evidence"),
    )


class TransactionalCreditLot(db.Model):
    """Exact credit contribution: remaining_amount / immutable policy threshold.

    Store the numerator, never a rounded fractional credit. Conversion consumes
    a complete threshold using FIFO contributions of the same policy version.
    """
    __tablename__ = "transactional_credit_lots"
    id = db.Column(db.Integer, primary_key=True)
    commission_id = db.Column(db.Integer, db.ForeignKey("transactional_commissions.id", ondelete="RESTRICT"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id", ondelete="RESTRICT"), nullable=False, index=True)
    policy_version = db.Column(db.String(80), db.ForeignKey("transactional_credit_policies.version", ondelete="RESTRICT"), nullable=False)
    original_amount = db.Column(ExactCreditAmount(), nullable=False)
    remaining_amount = db.Column(ExactCreditAmount(), nullable=False)
    credited_at = db.Column(db.DateTime, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    __table_args__ = (
        db.UniqueConstraint("commission_id", name="uq_credit_lot_commission"),
        db.CheckConstraint("CAST(original_amount AS NUMERIC) > 0 AND CAST(original_amount AS NUMERIC) < 1e62 AND CAST(original_amount AS NUMERIC) = round(CAST(original_amount AS NUMERIC),2)", name="ck_credit_lot_amount"),
        db.CheckConstraint("CAST(remaining_amount AS NUMERIC) >= 0 AND CAST(remaining_amount AS NUMERIC) <= CAST(original_amount AS NUMERIC) AND CAST(remaining_amount AS NUMERIC) = round(CAST(remaining_amount AS NUMERIC),2)", name="ck_credit_lot_remaining"),
        db.CheckConstraint("expires_at > credited_at", name="ck_credit_lot_expiry"),
        db.CheckConstraint("expires_at = credited_at + interval '40 days'", name="ck_credit_lot_40_days").ddl_if(dialect="postgresql"),
        db.CheckConstraint("abs(julianday(expires_at) - julianday(credited_at) - 40) < 0.00000001", name="ck_credit_lot_40_days").ddl_if(dialect="sqlite"),
    )


class PaymentEffectPaymentClaim(db.Model):
    """A financial payment cannot fund two different contractual orders."""
    __tablename__ = "payment_effect_payment_claims"
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(32), nullable=False)
    live_mode = db.Column(db.Boolean, nullable=False)
    external_payment_id = db.Column(db.String(160), nullable=False)
    payment_order_id = db.Column(db.Integer, db.ForeignKey("payment_orders.id", ondelete="RESTRICT"), nullable=False)
    evidence_id = db.Column(db.Integer, db.ForeignKey("payment_order_reconciliation_evidence.id", ondelete="RESTRICT"), nullable=False)
    __table_args__ = (db.UniqueConstraint("provider", "live_mode", "external_payment_id", name="uq_payment_effect_financial_payment"),)


class TransactionalCreditGrant(db.Model):
    __tablename__ = "transactional_credit_grants"
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id", ondelete="RESTRICT"), nullable=False)
    policy_version = db.Column(db.String(80), db.ForeignKey("transactional_credit_policies.version", ondelete="RESTRICT"), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey("subscriptions.id", ondelete="RESTRICT"), nullable=False)
    starts_at = db.Column(db.DateTime, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    credits_consumed = db.Column(db.Integer, nullable=False)
    __table_args__ = (
        db.UniqueConstraint("subscription_id", name="uq_credit_grant_subscription"),
        db.UniqueConstraint("professional_id", "starts_at", name="uq_credit_grant_period"),
        db.CheckConstraint("credits_consumed = 1", name="ck_credit_grant_one_credit"),
        db.CheckConstraint("expires_at > starts_at", name="ck_credit_grant_expiry"),
        db.CheckConstraint("expires_at = starts_at + interval '30 days'", name="ck_credit_grant_30_days").ddl_if(dialect="postgresql"),
        db.CheckConstraint("abs(julianday(expires_at) - julianday(starts_at) - 30) < 0.00000001", name="ck_credit_grant_30_days").ddl_if(dialect="sqlite"),
    )


class TransactionalCreditAllocation(db.Model):
    __tablename__ = "transactional_credit_allocations"
    id = db.Column(db.Integer, primary_key=True)
    grant_id = db.Column(db.Integer, db.ForeignKey("transactional_credit_grants.id", ondelete="RESTRICT"), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey("transactional_credit_lots.id", ondelete="RESTRICT"), nullable=False)
    amount = db.Column(ExactCreditAmount(), nullable=False)
    __table_args__ = (
        db.UniqueConstraint("grant_id", "lot_id", name="uq_credit_allocation"),
        db.CheckConstraint("CAST(amount AS NUMERIC) > 0 AND CAST(amount AS NUMERIC) = round(CAST(amount AS NUMERIC),2)", name="ck_credit_allocation_amount"),
    )


class PaymentEffectAudit(db.Model):
    __tablename__ = "payment_effect_audit"
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id", ondelete="RESTRICT"), nullable=False)
    evidence_id = db.Column(db.Integer, db.ForeignKey("payment_order_reconciliation_evidence.id", ondelete="RESTRICT"))
    grant_id = db.Column(db.Integer, db.ForeignKey("transactional_credit_grants.id", ondelete="RESTRICT"))
    operation = db.Column(db.String(40), nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False)
