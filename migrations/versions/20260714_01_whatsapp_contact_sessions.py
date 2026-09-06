"""whatsapp contact sessions

Revision ID: 20260714_01
Revises: 20260713_01
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260714_01"
down_revision = "20260713_01"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("whatsapp_contact_sessions"):
        return

    op.create_table(
        "whatsapp_contact_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_user_id", sa.Integer(), nullable=True),
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("operation_type", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("consent_given", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("consent_at", sa.DateTime(), nullable=True),
        sa.Column("initiated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_status_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["client_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["professional_id"], ["professionals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_whatsapp_contact_sessions_client_user_id", "whatsapp_contact_sessions", ["client_user_id"])
    op.create_index("ix_whatsapp_contact_sessions_entity_id", "whatsapp_contact_sessions", ["entity_id"])
    op.create_index("ix_whatsapp_contact_sessions_entity_type", "whatsapp_contact_sessions", ["entity_type"])
    op.create_index("ix_whatsapp_contact_sessions_initiated_at", "whatsapp_contact_sessions", ["initiated_at"])
    op.create_index("ix_whatsapp_contact_sessions_operation_type", "whatsapp_contact_sessions", ["operation_type"])
    op.create_index("ix_whatsapp_contact_sessions_professional_id", "whatsapp_contact_sessions", ["professional_id"])
    op.create_index("ix_whatsapp_contact_sessions_status", "whatsapp_contact_sessions", ["status"])


def downgrade():
    op.drop_index("ix_whatsapp_contact_sessions_status", table_name="whatsapp_contact_sessions")
    op.drop_index("ix_whatsapp_contact_sessions_professional_id", table_name="whatsapp_contact_sessions")
    op.drop_index("ix_whatsapp_contact_sessions_operation_type", table_name="whatsapp_contact_sessions")
    op.drop_index("ix_whatsapp_contact_sessions_initiated_at", table_name="whatsapp_contact_sessions")
    op.drop_index("ix_whatsapp_contact_sessions_entity_type", table_name="whatsapp_contact_sessions")
    op.drop_index("ix_whatsapp_contact_sessions_entity_id", table_name="whatsapp_contact_sessions")
    op.drop_index("ix_whatsapp_contact_sessions_client_user_id", table_name="whatsapp_contact_sessions")
    op.drop_table("whatsapp_contact_sessions")
