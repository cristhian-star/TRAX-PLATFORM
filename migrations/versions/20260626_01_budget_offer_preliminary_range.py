"""Add preliminary range fields to budget offers.

Revision ID: 20260626_01
Revises: 20260614_01
Create Date: 2026-06-26
"""

from alembic import op
import sqlalchemy as sa


revision = "20260626_01"
down_revision = "20260614_01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "budget_offers",
        sa.Column(
            "cobra_visita",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "budget_offers",
        sa.Column("precio_visita", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        "budget_offers",
        sa.Column("monto_desde", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        "budget_offers",
        sa.Column("monto_hasta", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.execute(
        """
        UPDATE budget_offers
        SET monto_desde = monto,
            monto_hasta = monto
        WHERE monto_desde IS NULL
           OR monto_hasta IS NULL
        """
    )

def downgrade():
    op.drop_column("budget_offers", "monto_hasta")
    op.drop_column("budget_offers", "monto_desde")
    op.drop_column("budget_offers", "precio_visita")
    op.drop_column("budget_offers", "cobra_visita")
