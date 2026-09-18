"""Durable internal transactional credit effects; no commercial defaults."""
from alembic import op
import sqlalchemy as sa

revision = "20260917_03"
down_revision = "20260917_02"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('transactional_credit_policies',
        sa.Column('version', sa.String(length=80), primary_key=True),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('threshold', sa.Numeric(64, 2).with_variant(sa.String(66), "sqlite"), nullable=False),
        sa.CheckConstraint("currency = 'ARS'", name='ck_credit_policy_currency'),
        sa.CheckConstraint('CAST(threshold AS NUMERIC) > 0 AND CAST(threshold AS NUMERIC) < 1e62 AND CAST(threshold AS NUMERIC) = round(CAST(threshold AS NUMERIC),2)', name='ck_credit_policy_threshold'),
    )
    op.create_table('payment_effect_decisions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('evidence_id', sa.Integer(), sa.ForeignKey('payment_order_reconciliation_evidence.id', ondelete="RESTRICT"), nullable=False),
        sa.Column('status', sa.String(length=24), nullable=False),
        sa.Column('reason', sa.String(length=40), nullable=False),
        sa.Column('observed_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('evidence_id', name='uq_payment_effect_evidence'),
        sa.CheckConstraint("status IN ('PENDING_POLICY','PENDING_REVIEW','NOT_ELIGIBLE','ACCRUED','REPLAY','EXEMPT')", name='ck_effect_decision_status'),
    )
    op.create_table('transactional_commissions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('payment_order_id', sa.Integer(), sa.ForeignKey('payment_orders.id', ondelete="RESTRICT"), nullable=False),
        sa.Column('evidence_id', sa.Integer(), sa.ForeignKey('payment_order_reconciliation_evidence.id', ondelete="RESTRICT"), nullable=False),
        sa.Column('professional_id', sa.Integer(), sa.ForeignKey('professionals.id', ondelete="RESTRICT"), nullable=False),
        sa.Column('status', sa.String(length=24), nullable=False),
        sa.Column('policy_version', sa.String(length=80), sa.ForeignKey('transactional_credit_policies.version', ondelete="RESTRICT"), nullable=True),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('live_mode', sa.Boolean(), nullable=False),
        sa.Column('external_identity', sa.String(length=160), nullable=True),
        sa.Column('net_amount', sa.Numeric(64, 2).with_variant(sa.String(66), "sqlite"), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('effective_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('payment_order_id', name='uq_commission_order'),
        sa.CheckConstraint("(status = 'EFFECTIVE' AND net_amount IS NOT NULL AND CAST(net_amount AS NUMERIC) > 0 AND currency = 'ARS' AND policy_version IS NOT NULL AND external_identity IS NOT NULL AND effective_at IS NOT NULL AND paid_at IS NOT NULL) OR (status <> 'EFFECTIVE' AND CAST(net_amount AS NUMERIC) IS NULL)", name='ck_commission_evidence'),
        sa.CheckConstraint("status IN ('PENDING_POLICY','PENDING_REVIEW','EFFECTIVE','EXEMPT')", name='ck_commission_status'),
        sa.UniqueConstraint('provider', 'live_mode', 'external_identity', name='uq_commission_financial_identity'),
    )
    op.create_table('payment_effect_payment_claims',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('provider', sa.String(32), nullable=False),
        sa.Column('live_mode', sa.Boolean(), nullable=False),
        sa.Column('external_payment_id', sa.String(160), nullable=False),
        sa.Column('payment_order_id', sa.Integer(), sa.ForeignKey('payment_orders.id', ondelete="RESTRICT"), nullable=False),
        sa.Column('evidence_id', sa.Integer(), sa.ForeignKey('payment_order_reconciliation_evidence.id', ondelete="RESTRICT"), nullable=False),
        sa.UniqueConstraint('provider','live_mode','external_payment_id',name='uq_payment_effect_financial_payment'),
    )
    op.create_table('transactional_credit_lots',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('commission_id', sa.Integer(), sa.ForeignKey('transactional_commissions.id', ondelete="RESTRICT"), nullable=False),
        sa.Column('professional_id', sa.Integer(), sa.ForeignKey('professionals.id', ondelete="RESTRICT"), nullable=False),
        sa.Column('policy_version', sa.String(length=80), sa.ForeignKey('transactional_credit_policies.version', ondelete="RESTRICT"), nullable=False),
        sa.Column('original_amount', sa.Numeric(64, 2).with_variant(sa.String(66), "sqlite"), nullable=False),
        sa.Column('remaining_amount', sa.Numeric(64, 2).with_variant(sa.String(66), "sqlite"), nullable=False),
        sa.Column('credited_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('commission_id', name='uq_credit_lot_commission'),
        sa.CheckConstraint('CAST(original_amount AS NUMERIC) > 0 AND CAST(original_amount AS NUMERIC) < 1e62 AND CAST(original_amount AS NUMERIC) = round(CAST(original_amount AS NUMERIC),2)', name='ck_credit_lot_amount'),
        sa.CheckConstraint('expires_at > credited_at', name='ck_credit_lot_expiry'),
        sa.CheckConstraint("expires_at = credited_at + interval '40 days'" if op.get_bind().dialect.name == 'postgresql' else "abs(julianday(expires_at) - julianday(credited_at) - 40) < 0.00000001", name='ck_credit_lot_40_days'),
        sa.CheckConstraint('CAST(remaining_amount AS NUMERIC) >= 0 AND CAST(remaining_amount AS NUMERIC) <= CAST(original_amount AS NUMERIC) AND CAST(remaining_amount AS NUMERIC) = round(CAST(remaining_amount AS NUMERIC),2)', name='ck_credit_lot_remaining'),
    )
    op.create_index('ix_transactional_credit_lots_professional_id', 'transactional_credit_lots', ['professional_id'])
    op.create_table('transactional_credit_grants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('professional_id', sa.Integer(), sa.ForeignKey('professionals.id', ondelete="RESTRICT"), nullable=False),
        sa.Column('policy_version', sa.String(length=80), sa.ForeignKey('transactional_credit_policies.version', ondelete="RESTRICT"), nullable=False),
        sa.Column('subscription_id', sa.Integer(), sa.ForeignKey('subscriptions.id', ondelete="RESTRICT"), nullable=False),
        sa.Column('starts_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('credits_consumed', sa.Integer(), nullable=False),
        sa.UniqueConstraint('subscription_id', name='uq_credit_grant_subscription'),
        sa.CheckConstraint('expires_at > starts_at', name='ck_credit_grant_expiry'),
        sa.CheckConstraint("expires_at = starts_at + interval '30 days'" if op.get_bind().dialect.name == 'postgresql' else "abs(julianday(expires_at) - julianday(starts_at) - 30) < 0.00000001", name='ck_credit_grant_30_days'),
        sa.CheckConstraint('credits_consumed = 1', name='ck_credit_grant_one_credit'),
        sa.UniqueConstraint('professional_id', 'starts_at', name='uq_credit_grant_period'),
    )
    op.create_table('transactional_credit_allocations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('grant_id', sa.Integer(), sa.ForeignKey('transactional_credit_grants.id', ondelete="RESTRICT"), nullable=False),
        sa.Column('lot_id', sa.Integer(), sa.ForeignKey('transactional_credit_lots.id', ondelete="RESTRICT"), nullable=False),
        sa.Column('amount', sa.Numeric(64, 2).with_variant(sa.String(66), "sqlite"), nullable=False),
        sa.CheckConstraint('CAST(amount AS NUMERIC) > 0 AND CAST(amount AS NUMERIC) = round(CAST(amount AS NUMERIC),2)', name='ck_credit_allocation_amount'),
        sa.UniqueConstraint('grant_id', 'lot_id', name='uq_credit_allocation'),
    )
    op.create_table('payment_effect_audit',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('professional_id', sa.Integer(), sa.ForeignKey('professionals.id', ondelete="RESTRICT"), nullable=False),
        sa.Column('evidence_id', sa.Integer(), sa.ForeignKey('payment_order_reconciliation_evidence.id', ondelete="RESTRICT"), nullable=True),
        sa.Column('grant_id', sa.Integer(), sa.ForeignKey('transactional_credit_grants.id', ondelete="RESTRICT"), nullable=True),
        sa.Column('operation', sa.String(length=40), nullable=False),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
    )


def downgrade():
    # Dropping funded provenance while keeping PRO would silently orphan rights.
    if op.get_context().as_sql:
        raise RuntimeError("credit ledger downgrade requires an online data check")
    for table in (
        'payment_effect_audit', 'transactional_credit_allocations', 'transactional_credit_grants',
        'transactional_credit_lots', 'payment_effect_payment_claims', 'transactional_commissions',
        'payment_effect_decisions',
    ):
        if op.get_bind().execute(sa.text(f'SELECT 1 FROM {table} LIMIT 1')).first():
            raise RuntimeError("populated credit ledger downgrade requires a separate preservation plan")
    op.drop_table('payment_effect_audit')
    op.drop_table('transactional_credit_allocations')
    op.drop_table('transactional_credit_grants')
    op.drop_table('transactional_credit_lots')
    op.drop_table('payment_effect_payment_claims')
    op.drop_table('transactional_commissions')
    op.drop_table('payment_effect_decisions')
    op.drop_table('transactional_credit_policies')
