"""Add budget marketplace requests and offers.

Revision ID: 20260614_01
Revises: 20260607_01
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260614_01"
down_revision = "20260607_01"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    request_columns = {
        column["name"]
        for column in inspector.get_columns("budget_requests")
    }

    if "titulo" not in request_columns:
        op.add_column(
            "budget_requests",
            sa.Column("titulo", sa.String(length=160), nullable=True),
        )
    if "fecha_estimada" not in request_columns:
        op.add_column(
            "budget_requests",
            sa.Column("fecha_estimada", sa.Date(), nullable=True),
        )
    if "urgencia" not in request_columns:
        op.add_column(
            "budget_requests",
            sa.Column(
                "urgencia",
                sa.String(length=50),
                nullable=False,
                server_default="NORMAL",
            ),
        )

    op.execute(
        """
        UPDATE budget_requests
        SET titulo = CASE
            WHEN categoria IS NOT NULL AND categoria <> ''
                THEN 'Solicitud de ' || categoria
            ELSE 'Solicitud de presupuesto'
        END
        WHERE titulo IS NULL
        """
    )
    with op.batch_alter_table("budget_requests") as batch_op:
        batch_op.alter_column(
            "titulo",
            existing_type=sa.String(length=160),
            nullable=False,
        )
        batch_op.alter_column(
            "urgencia",
            existing_type=sa.String(length=50),
            existing_nullable=False,
            server_default=None,
        )

    inspector = sa.inspect(connection)
    if "budget_offers" not in inspector.get_table_names():
        op.create_table(
            "budget_offers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("budget_request_id", sa.Integer(), nullable=False),
            sa.Column("professional_id", sa.Integer(), nullable=False),
            sa.Column("professional_user_id", sa.Integer(), nullable=False),
            sa.Column("monto", sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column("mensaje", sa.Text(), nullable=False),
            sa.Column("plazo_estimado", sa.String(length=120), nullable=False),
            sa.Column("condiciones", sa.Text(), nullable=True),
            sa.Column(
                "estado",
                sa.String(length=50),
                nullable=False,
                server_default="ENVIADO",
            ),
            sa.Column(
                "fecha_creacion",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.ForeignKeyConstraint(["budget_request_id"], ["budget_requests.id"]),
            sa.ForeignKeyConstraint(["professional_id"], ["professionals.id"]),
            sa.ForeignKeyConstraint(["professional_user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "budget_request_id",
                "professional_id",
                name="uq_budget_offer_request_professional",
            ),
        )
        op.create_index(
            op.f("ix_budget_offers_budget_request_id"),
            "budget_offers",
            ["budget_request_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_budget_offers_professional_id"),
            "budget_offers",
            ["professional_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_budget_offers_professional_user_id"),
            "budget_offers",
            ["professional_user_id"],
            unique=False,
        )


def downgrade():
    op.drop_index(
        op.f("ix_budget_offers_professional_user_id"),
        table_name="budget_offers",
    )
    op.drop_index(
        op.f("ix_budget_offers_professional_id"),
        table_name="budget_offers",
    )
    op.drop_index(
        op.f("ix_budget_offers_budget_request_id"),
        table_name="budget_offers",
    )
    op.drop_table("budget_offers")
    op.drop_column("budget_requests", "urgencia")
    op.drop_column("budget_requests", "fecha_estimada")
    op.drop_column("budget_requests", "titulo")
