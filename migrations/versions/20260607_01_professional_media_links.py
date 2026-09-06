"""Add professional media and external link URLs.

Revision ID: 20260607_01
Revises: 20260527_01
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20260607_01"
down_revision = "20260527_01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("professionals", sa.Column("logo_url", sa.Text(), nullable=True))
    op.add_column("professionals", sa.Column("cover_url", sa.Text(), nullable=True))
    op.add_column("professionals", sa.Column("gallery_urls", sa.Text(), nullable=True))
    op.add_column("professionals", sa.Column("google_drive_url", sa.Text(), nullable=True))
    op.add_column("professionals", sa.Column("website_url", sa.Text(), nullable=True))
    op.add_column("professionals", sa.Column("instagram_url", sa.Text(), nullable=True))
    op.add_column("professionals", sa.Column("tiktok_url", sa.Text(), nullable=True))
    op.add_column("professionals", sa.Column("youtube_url", sa.Text(), nullable=True))
    op.add_column("professionals", sa.Column("other_links", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("professionals", "other_links")
    op.drop_column("professionals", "youtube_url")
    op.drop_column("professionals", "tiktok_url")
    op.drop_column("professionals", "instagram_url")
    op.drop_column("professionals", "website_url")
    op.drop_column("professionals", "google_drive_url")
    op.drop_column("professionals", "gallery_urls")
    op.drop_column("professionals", "cover_url")
    op.drop_column("professionals", "logo_url")
