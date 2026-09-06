"""activity notifications v1

Revision ID: 20260712_01
Revises: 20260627_01
Create Date: 2026-07-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20260712_01"
down_revision = "20260627_01"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("activity_notifications"):
        return

    op.create_table(
        "activity_notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("tipo", sa.String(length=80), nullable=False),
        sa.Column("categoria", sa.String(length=50), nullable=False),
        sa.Column("titulo", sa.String(length=180), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("url_destino", sa.String(length=255), nullable=True),
        sa.Column("entity_type", sa.String(length=80), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("prioridad", sa.String(length=50), nullable=False, server_default="INFO"),
        sa.Column("requiere_accion", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("leida", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_notifications_actor_user_id", "activity_notifications", ["actor_user_id"])
    op.create_index("ix_activity_notifications_categoria", "activity_notifications", ["categoria"])
    op.create_index("ix_activity_notifications_created_at", "activity_notifications", ["created_at"])
    op.create_index("ix_activity_notifications_entity_id", "activity_notifications", ["entity_id"])
    op.create_index("ix_activity_notifications_entity_type", "activity_notifications", ["entity_type"])
    op.create_index("ix_activity_notifications_leida", "activity_notifications", ["leida"])
    op.create_index("ix_activity_notifications_prioridad", "activity_notifications", ["prioridad"])
    op.create_index("ix_activity_notifications_tipo", "activity_notifications", ["tipo"])
    op.create_index("ix_activity_notifications_user_id", "activity_notifications", ["user_id"])


def downgrade():
    op.drop_index("ix_activity_notifications_user_id", table_name="activity_notifications")
    op.drop_index("ix_activity_notifications_tipo", table_name="activity_notifications")
    op.drop_index("ix_activity_notifications_prioridad", table_name="activity_notifications")
    op.drop_index("ix_activity_notifications_leida", table_name="activity_notifications")
    op.drop_index("ix_activity_notifications_entity_type", table_name="activity_notifications")
    op.drop_index("ix_activity_notifications_entity_id", table_name="activity_notifications")
    op.drop_index("ix_activity_notifications_created_at", table_name="activity_notifications")
    op.drop_index("ix_activity_notifications_categoria", table_name="activity_notifications")
    op.drop_index("ix_activity_notifications_actor_user_id", table_name="activity_notifications")
    op.drop_table("activity_notifications")
