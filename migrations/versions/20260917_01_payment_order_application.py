"""Link final obligations to contracts and reserve payment order creation.

Revision ID: 20260917_01
Revises: 20260916_01
"""
from alembic import op
import sqlalchemy as sa


revision = "20260917_01"
down_revision = "20260916_01"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("payment_obligations") as batch:
        batch.add_column(sa.Column("contract_request_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_payment_obligations_contract_request", "contract_requests",
            ["contract_request_id"], ["id"], ondelete="RESTRICT",
        )
        batch.create_unique_constraint("uq_payment_obligations_contract_request", ["contract_request_id"])
    expiry = (
        "expires_at = created_at + interval '72 hours'"
        if op.get_bind().dialect.name == "postgresql" else
        "abs((julianday(expires_at) - julianday(created_at)) - 3.0) < 0.00000001"
    )
    op.create_table(
        "payment_order_reservations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("obligation_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("payment_order_id", sa.Integer(), nullable=True),
        sa.Column("local_order_id", sa.String(160), nullable=False),
        sa.Column("obligation_reference", sa.String(160), nullable=False),
        sa.Column("external_reference", sa.String(160), nullable=False),
        sa.Column("idempotency_key", sa.String(160), nullable=False),
        sa.Column("amount", sa.Numeric(), nullable=False),
        sa.Column("currency", sa.String(16), nullable=False),
        sa.Column("concept", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["obligation_id"], ["payment_obligations.id"], ondelete="RESTRICT", name="fk_payment_order_reservations_obligation"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT", name="fk_payment_order_reservations_actor"),
        sa.ForeignKeyConstraint(["professional_id"], ["professionals.id"], ondelete="RESTRICT", name="fk_payment_order_reservations_professional"),
        sa.ForeignKeyConstraint(["payment_order_id"], ["payment_orders.id"], ondelete="RESTRICT", name="fk_payment_order_reservations_order"),
        sa.UniqueConstraint("obligation_id", name="uq_payment_order_reservations_obligation"),
        sa.UniqueConstraint("local_order_id", name="uq_payment_order_reservations_local_order"),
        sa.UniqueConstraint("idempotency_key", name="uq_payment_order_reservations_idempotency"),
        sa.UniqueConstraint("external_reference", name="uq_payment_order_reservations_external_reference"),
        sa.UniqueConstraint("payment_order_id", name="uq_payment_order_reservations_order"),
        sa.CheckConstraint("status IN ('PREPARED','CALL_IN_PROGRESS','SUCCEEDED','UNCERTAIN')", name="ck_payment_order_reservations_status"),
        sa.CheckConstraint(
            "(status IN ('PREPARED','CALL_IN_PROGRESS') AND payment_order_id IS NULL AND finished_at IS NULL) OR "
            "(status = 'UNCERTAIN' AND payment_order_id IS NULL AND finished_at IS NOT NULL) OR "
            "(status = 'SUCCEEDED' AND payment_order_id IS NOT NULL AND finished_at IS NOT NULL)",
            name="ck_payment_order_reservations_completion",
        ),
        sa.CheckConstraint("amount > 0 AND amount < 1e62 AND amount = round(amount, 2)", name="ck_payment_order_reservations_amount"),
        sa.CheckConstraint("currency = 'ARS'", name="ck_payment_order_reservations_currency"),
        sa.CheckConstraint(expiry, name="ck_payment_order_reservations_expiry"),
    )


def downgrade():
    op.drop_table("payment_order_reservations")
    with op.batch_alter_table("payment_obligations") as batch:
        batch.drop_constraint("uq_payment_obligations_contract_request", type_="unique")
        batch.drop_constraint("fk_payment_obligations_contract_request", type_="foreignkey")
        batch.drop_column("contract_request_id")
