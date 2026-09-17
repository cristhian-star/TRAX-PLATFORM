"""Add durable payment order persistence foundation.

Revision ID: 20260916_01
Revises: 20260911_02
"""
from alembic import op
import sqlalchemy as sa


revision = "20260916_01"
down_revision = "20260911_02"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    expiry_check = (
        "expires_at = created_at + interval '72 hours'"
        if bind.dialect.name == "postgresql"
        else "abs((julianday(expires_at) - julianday(created_at)) - 3.0) < 0.00000001"
    )
    op.create_table(
        "payment_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("obligation_id", sa.Integer(), nullable=False),
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("local_order_id", sa.String(160), nullable=False),
        sa.Column("external_reference", sa.String(160), nullable=False),
        sa.Column("idempotency_key", sa.String(160), nullable=False),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.Column("currency", sa.String(16), nullable=False),
        sa.Column("concept", sa.String(200), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("live_mode", sa.Boolean(), nullable=False),
        sa.Column("external_order_id", sa.String(160), nullable=False),
        sa.Column("checkout_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("amount > 0 AND amount < 1e62 AND amount = round(amount, 2)", name="ck_payment_orders_amount_valid"),
        sa.CheckConstraint("currency = 'ARS'", name="ck_payment_orders_currency_ars"),
        sa.CheckConstraint("status IN ('ACTIVE','EXPIRED','CANCELLED')", name="ck_payment_orders_status_valid"),
        sa.CheckConstraint(expiry_check, name="ck_payment_orders_expiry_72h"),
        sa.CheckConstraint(
            "(status = 'ACTIVE' AND closed_at IS NULL AND cancelled_at IS NULL) OR "
            "(status = 'EXPIRED' AND closed_at IS NOT NULL AND "
            "closed_at = expires_at AND cancelled_at IS NULL) OR "
            "(status = 'CANCELLED' AND closed_at IS NOT NULL AND "
            "cancelled_at IS NOT NULL AND closed_at = cancelled_at AND "
            "cancelled_at >= created_at AND cancelled_at < expires_at)",
            name="ck_payment_orders_status_timestamps_coherent",
        ),
        sa.ForeignKeyConstraint(["obligation_id"], ["payment_obligations.id"], name="fk_payment_orders_obligation", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["professional_id"], ["professionals.id"], name="fk_payment_orders_professional", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("local_order_id", name="uq_payment_orders_local_order_id"),
        sa.UniqueConstraint("idempotency_key", name="uq_payment_orders_idempotency_key"),
        sa.UniqueConstraint("external_reference", name="uq_payment_orders_external_reference"),
        sa.UniqueConstraint("provider", "live_mode", "external_order_id", name="uq_payment_orders_psp_identity"),
    )
    op.create_index("ix_payment_orders_obligation_id", "payment_orders", ["obligation_id"])
    op.create_index("ix_payment_orders_professional_id", "payment_orders", ["professional_id"])
    op.create_index(
        "uq_payment_orders_active_obligation", "payment_orders", ["obligation_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
        sqlite_where=sa.text("status = 'ACTIVE'"),
    )


def downgrade():
    op.drop_index("uq_payment_orders_active_obligation", table_name="payment_orders")
    op.drop_index("ix_payment_orders_professional_id", table_name="payment_orders")
    op.drop_index("ix_payment_orders_obligation_id", table_name="payment_orders")
    op.drop_table("payment_orders")
