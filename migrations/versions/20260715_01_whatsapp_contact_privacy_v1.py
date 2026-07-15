"""whatsapp contact privacy v1

Revision ID: 20260715_01
Revises: 20260714_01
Create Date: 2026-07-15
"""

from alembic import op
import sqlalchemy as sa


revision = "20260715_01"
down_revision = "20260714_01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("professionals", sa.Column("whatsapp_username", sa.String(length=64), nullable=True))
    op.add_column(
        "professionals",
        sa.Column(
            "whatsapp_contact_preference",
            sa.String(length=20),
            nullable=False,
            server_default="AUTO",
        ),
    )
    op.add_column(
        "whatsapp_contact_sessions",
        sa.Column("contact_identifier_type", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "whatsapp_contact_sessions",
        sa.Column("contact_identifier_masked", sa.String(length=120), nullable=True),
    )


def downgrade():
    op.drop_column("whatsapp_contact_sessions", "contact_identifier_masked")
    op.drop_column("whatsapp_contact_sessions", "contact_identifier_type")
    op.drop_column("professionals", "whatsapp_contact_preference")
    op.drop_column("professionals", "whatsapp_username")
