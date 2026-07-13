"""google maps coverage v2

Revision ID: 20260713_01
Revises: 20260712_02
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa


revision = "20260713_01"
down_revision = "20260712_02"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name, column_name):
    return column_name in {
        column["name"] for column in inspector.get_columns(table_name)
    }


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("professionals"):
        return

    if not _has_column(inspector, "professionals", "coverage_location_consent_at"):
        op.add_column(
            "professionals",
            sa.Column("coverage_location_consent_at", sa.DateTime(), nullable=True),
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("professionals") and _has_column(
        inspector,
        "professionals",
        "coverage_location_consent_at",
    ):
        op.drop_column("professionals", "coverage_location_consent_at")
