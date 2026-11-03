"""Internal fiscal declarations and drafts; no ARCA authorization.

Revision ID: 20261101_01
Revises: 20261030_01
"""
from alembic import op
import sqlalchemy as sa

revision = "20261101_01"
down_revision = "20261030_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("billing_profiles",
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("cuit", sa.String(11), nullable=False),
        sa.Column("legal_name", sa.String(200), nullable=False),
        sa.Column("fiscal_address", sa.String(300), nullable=False),
        sa.Column("verification_status", sa.String(24), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("verification_status = 'DECLARED_UNVERIFIED'", name="ck_billing_profile_declared"),
        sa.CheckConstraint("version >= 1", name="ck_billing_profile_version"))
    op.create_table("billing_drafts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("billing_profiles.owner_user_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("request_key", sa.String(36), nullable=False),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("recipient_name", sa.String(200), nullable=False),
        sa.Column("service_from", sa.Date(), nullable=False),
        sa.Column("service_to", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.UniqueConstraint("owner_user_id", "request_key", name="uq_billing_draft_request"),
        sa.CheckConstraint("status = 'INTERNAL_DRAFT'", name="ck_billing_draft_internal"),
        sa.CheckConstraint("amount > 0 AND amount <= 999999999999.99", name="ck_billing_draft_amount"),
        sa.CheckConstraint("service_from <= service_to", name="ck_billing_draft_period"),
        sa.CheckConstraint("profile_version >= 1", name="ck_billing_draft_profile_version"))


def downgrade():
    # Destructive: export and approve loss of all internal drafts/profiles first.
    op.drop_table("billing_drafts")
    op.drop_table("billing_profiles")
