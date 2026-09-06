"""smart coverage v1

Revision ID: 20260712_02
Revises: 20260712_01
Create Date: 2026-07-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260712_02"
down_revision = "20260712_01"
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

    columns = (
        ("coverage_location", sa.Column("coverage_location", sa.String(length=160), nullable=True)),
        ("coverage_city", sa.Column("coverage_city", sa.String(length=120), nullable=True)),
        ("coverage_province", sa.Column("coverage_province", sa.String(length=120), nullable=True)),
        ("coverage_radius_km", sa.Column("coverage_radius_km", sa.Integer(), nullable=True)),
        ("coverage_mode", sa.Column("coverage_mode", sa.String(length=50), nullable=True)),
        ("coverage_notes", sa.Column("coverage_notes", sa.Text(), nullable=True)),
        ("latitude", sa.Column("latitude", sa.Float(), nullable=True)),
        ("longitude", sa.Column("longitude", sa.Float(), nullable=True)),
    )

    for column_name, column in columns:
        if not _has_column(inspector, "professionals", column_name):
            op.add_column("professionals", column)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("professionals"):
        return

    for column_name in (
        "longitude",
        "latitude",
        "coverage_notes",
        "coverage_mode",
        "coverage_radius_km",
        "coverage_province",
        "coverage_city",
        "coverage_location",
    ):
        if _has_column(inspector, "professionals", column_name):
            op.drop_column("professionals", column_name)
