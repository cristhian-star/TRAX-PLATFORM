"""Add contextual PSP identity to payment attempts.

Revision ID: 20260911_02
Revises: 20260911_01
"""
from alembic import op
import sqlalchemy as sa


revision = "20260911_02"
down_revision = "20260911_01"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("payment_attempts") as batch:
        batch.add_column(sa.Column("psp_provider", sa.String(64), nullable=True))
        batch.add_column(sa.Column("psp_live_mode", sa.Boolean(), nullable=True))
        batch.create_check_constraint(
            "ck_payment_attempts_psp_context_complete",
            "(psp_provider IS NULL AND psp_live_mode IS NULL) OR "
            "(psp_provider IS NOT NULL AND psp_live_mode IS NOT NULL)",
        )
    op.create_index(
        "uq_payment_attempts_psp_identity",
        "payment_attempts",
        ["psp_provider", "psp_live_mode", "external_attempt_id"],
        unique=True,
        postgresql_where=sa.text(
            "psp_provider IS NOT NULL AND psp_live_mode IS NOT NULL "
            "AND external_attempt_id IS NOT NULL"
        ),
        sqlite_where=sa.text(
            "psp_provider IS NOT NULL AND psp_live_mode IS NOT NULL "
            "AND external_attempt_id IS NOT NULL"
        ),
    )


def downgrade():
    op.drop_index("uq_payment_attempts_psp_identity", table_name="payment_attempts")
    with op.batch_alter_table("payment_attempts") as batch:
        batch.drop_constraint("ck_payment_attempts_psp_context_complete", type_="check")
        batch.drop_column("psp_live_mode")
        batch.drop_column("psp_provider")
