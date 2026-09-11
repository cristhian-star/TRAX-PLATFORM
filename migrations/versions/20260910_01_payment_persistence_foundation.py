"""Add payment persistence foundation.

Revision ID: 20260910_01
Revises: 20260904_01
Create Date: 2026-09-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260910_01"
down_revision: Union[str, Sequence[str], None] = "20260904_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_obligations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("internal_reference", sa.String(length=160), nullable=False),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_payment_obligations_amount_positive"),
        sa.CheckConstraint("length(trim(currency)) > 0", name="ck_payment_obligations_currency_nonempty"),
        sa.CheckConstraint("length(trim(internal_reference)) > 0", name="ck_payment_obligations_reference_nonempty"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("internal_reference", name="uq_payment_obligations_reference"),
    )
    op.create_table(
        "payment_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("obligation_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("external_attempt_id", sa.String(length=255), nullable=True),
        sa.Column("financial_status", sa.String(length=32), nullable=True),
        sa.Column("orchestration_result", sa.String(length=32), nullable=False),
        sa.Column("requires_reconciliation", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("length(trim(idempotency_key)) > 0", name="ck_payment_attempts_key_nonempty"),
        sa.CheckConstraint("financial_status IS NULL OR financial_status IN ('APPROVED','REJECTED','PENDING')", name="ck_payment_attempts_financial_status_valid"),
        sa.CheckConstraint("orchestration_result IN ('APPROVED','REJECTED','PENDING','RECONCILIATION_REQUIRED')", name="ck_payment_attempts_result_valid"),
        sa.CheckConstraint("(orchestration_result = 'RECONCILIATION_REQUIRED' AND requires_reconciliation = true AND financial_status IS NULL) OR (orchestration_result <> 'RECONCILIATION_REQUIRED' AND requires_reconciliation = false AND financial_status = orchestration_result)", name="ck_payment_attempts_result_coherent"),
        sa.ForeignKeyConstraint(["obligation_id"], ["payment_obligations.id"], name="fk_payment_attempts_obligation", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_payment_attempts_idempotency_key"),
    )
    op.create_index("ix_payment_attempts_obligation_id", "payment_attempts", ["obligation_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_payment_attempts_obligation_id", table_name="payment_attempts")
    op.drop_table("payment_attempts")
    op.drop_table("payment_obligations")
