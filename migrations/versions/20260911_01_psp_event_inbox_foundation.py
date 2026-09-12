"""Add neutral PSP event inbox.

Revision ID: 20260911_01
Revises: 20260910_01
"""
from alembic import op
import sqlalchemy as sa


revision = "20260911_01"
down_revision = "20260910_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "psp_event_inbox",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("external_event_id", sa.String(255), nullable=False),
        sa.Column("topic", sa.String(128), nullable=False),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("external_resource_id", sa.String(255), nullable=False),
        sa.Column("test_mode", sa.Boolean(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "test_mode", "external_event_id", name="uq_psp_event_inbox_identity"),
        sa.CheckConstraint("length(trim(provider)) > 0", name="ck_psp_event_inbox_provider_nonempty"),
        sa.CheckConstraint("length(trim(external_event_id)) > 0", name="ck_psp_event_inbox_event_id_nonempty"),
        sa.CheckConstraint("length(trim(topic)) > 0", name="ck_psp_event_inbox_topic_nonempty"),
        sa.CheckConstraint("length(trim(action)) > 0", name="ck_psp_event_inbox_action_nonempty"),
        sa.CheckConstraint("length(trim(external_resource_id)) > 0", name="ck_psp_event_inbox_resource_id_nonempty"),
        sa.CheckConstraint("length(payload_hash) = 64", name="ck_psp_event_inbox_payload_hash_length"),
    )


def downgrade():
    op.drop_table("psp_event_inbox")
