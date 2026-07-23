"""professional media v1

Revision ID: 20260723_01
Revises: 20260715_01
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa


revision = "20260723_01"
down_revision = "20260715_01"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("professional_media"):
        return

    op.create_table(
        "professional_media",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=False),
        sa.Column("media_type", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("public_url", sa.Text(), nullable=False),
        sa.Column("secure_url", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.Text(), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("content_type", sa.String(length=80), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=140), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("alt_text", sa.String(length=180), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PUBLICADO"),
        sa.Column("moderation_reason", sa.Text(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["professional_id"], ["professionals.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
        sa.CheckConstraint("media_type in ('AVATAR', 'COVER', 'GALLERY')", name="ck_professional_media_type"),
        sa.CheckConstraint(
            "status in ('BORRADOR', 'PENDIENTE_MODERACION', 'PUBLICADO', 'RECHAZADO', 'OCULTO', 'ELIMINADO')",
            name="ck_professional_media_status",
        ),
        sa.CheckConstraint("file_size_bytes >= 0", name="ck_professional_media_file_size"),
        sa.CheckConstraint("width > 0", name="ck_professional_media_width"),
        sa.CheckConstraint("height > 0", name="ck_professional_media_height"),
    )
    op.create_index("ix_professional_media_category", "professional_media", ["category"])
    op.create_index("ix_professional_media_checksum_sha256", "professional_media", ["checksum_sha256"])
    op.create_index("ix_professional_media_created_at", "professional_media", ["created_at"])
    op.create_index("ix_professional_media_is_primary", "professional_media", ["is_primary"])
    op.create_index("ix_professional_media_media_type", "professional_media", ["media_type"])
    op.create_index("ix_professional_media_professional_id", "professional_media", ["professional_id"])
    op.create_index(
        "ix_professional_media_professional_sort",
        "professional_media",
        ["professional_id", "sort_order"],
    )
    op.create_index(
        "ix_professional_media_professional_type_status",
        "professional_media",
        ["professional_id", "media_type", "status"],
    )
    op.create_index("ix_professional_media_status", "professional_media", ["status"])
    op.create_index("ix_professional_media_uploaded_by_user_id", "professional_media", ["uploaded_by_user_id"])

    dialect = bind.dialect.name
    if dialect in ("postgresql", "sqlite"):
        op.create_index(
            "uq_professional_media_active_avatar",
            "professional_media",
            ["professional_id"],
            unique=True,
            postgresql_where=sa.text("media_type = 'AVATAR' AND deleted_at IS NULL AND status != 'ELIMINADO'"),
            sqlite_where=sa.text("media_type = 'AVATAR' AND deleted_at IS NULL AND status != 'ELIMINADO'"),
        )
        op.create_index(
            "uq_professional_media_active_cover",
            "professional_media",
            ["professional_id"],
            unique=True,
            postgresql_where=sa.text("media_type = 'COVER' AND deleted_at IS NULL AND status != 'ELIMINADO'"),
            sqlite_where=sa.text("media_type = 'COVER' AND deleted_at IS NULL AND status != 'ELIMINADO'"),
        )


def downgrade():
    op.drop_index("uq_professional_media_active_cover", table_name="professional_media")
    op.drop_index("uq_professional_media_active_avatar", table_name="professional_media")
    op.drop_index("ix_professional_media_uploaded_by_user_id", table_name="professional_media")
    op.drop_index("ix_professional_media_status", table_name="professional_media")
    op.drop_index("ix_professional_media_professional_type_status", table_name="professional_media")
    op.drop_index("ix_professional_media_professional_sort", table_name="professional_media")
    op.drop_index("ix_professional_media_professional_id", table_name="professional_media")
    op.drop_index("ix_professional_media_media_type", table_name="professional_media")
    op.drop_index("ix_professional_media_is_primary", table_name="professional_media")
    op.drop_index("ix_professional_media_created_at", table_name="professional_media")
    op.drop_index("ix_professional_media_checksum_sha256", table_name="professional_media")
    op.drop_index("ix_professional_media_category", table_name="professional_media")
    op.drop_table("professional_media")
