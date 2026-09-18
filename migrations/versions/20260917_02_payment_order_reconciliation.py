"""Durable Orders webhook work, attempts, quarantine and minimal evidence.

Revision ID: 20260917_02
Revises: 20260917_01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260917_02"
down_revision = "20260917_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "payment_order_reconciliation_work",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("psp_event_inbox.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=False),
        sa.Column("lease_token", sa.String(36)),
        sa.Column("lease_until", sa.DateTime()),
        sa.Column("last_error", sa.String(32)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("event_id", name="uq_order_reconciliation_event"),
        sa.CheckConstraint("attempt_count BETWEEN 0 AND 8", name="ck_order_work_attempts"),
        sa.CheckConstraint("status IN ('QUEUED','PROCESSING','DONE','QUARANTINED','EXHAUSTED')", name="ck_order_work_status"),
        sa.CheckConstraint("(status = 'PROCESSING' AND lease_token IS NOT NULL AND lease_until IS NOT NULL) OR (status <> 'PROCESSING' AND lease_token IS NULL AND lease_until IS NULL)", name="ck_order_work_lease"),
    )
    op.create_index("ix_payment_order_reconciliation_work_next_attempt_at", "payment_order_reconciliation_work", ["next_attempt_at"])
    op.create_table(
        "payment_order_reconciliation_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("work_id", sa.Integer(), sa.ForeignKey("payment_order_reconciliation_work.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("dispatched_at", sa.DateTime()),
        sa.Column("finished_at", sa.DateTime()),
        sa.Column("outcome", sa.String(24), nullable=False),
        sa.Column("error_code", sa.String(32)),
        sa.UniqueConstraint("work_id", "number", name="uq_order_reconciliation_attempt"),
        sa.CheckConstraint("number BETWEEN 1 AND 8", name="ck_order_attempt_number"),
        sa.CheckConstraint("outcome IN ('STARTED','RECONCILED','RETRY','QUARANTINED','EXHAUSTED','LEASE_LOST')", name="ck_order_attempt_outcome"),
    )
    op.create_table(
        "payment_order_reconciliation_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("payment_order_id", sa.Integer(), sa.ForeignKey("payment_orders.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("psp_event_inbox.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("payment_order_reconciliation_attempts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("snapshot_hash", sa.String(64), nullable=False),
        sa.Column("remote_updated_at", sa.DateTime(), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("timing", sa.String(24), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.UniqueConstraint("payment_order_id", "snapshot_hash", name="uq_order_evidence_snapshot"),
        sa.CheckConstraint("length(snapshot_hash) = 64", name="ck_order_evidence_hash"),
        sa.CheckConstraint("timing IN ('BEFORE_LOCAL_EXPIRY','AFTER_LOCAL_EXPIRY','UNKNOWN')", name="ck_order_evidence_timing"),
    )
    op.create_index("ix_payment_order_reconciliation_evidence_payment_order_id", "payment_order_reconciliation_evidence", ["payment_order_id"])
    op.create_table(
        "payment_order_reconciliation_quarantine",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("psp_event_inbox.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("reason", sa.String(32), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("event_id", "content_hash", "reason", name="uq_order_quarantine_content"),
        sa.CheckConstraint("length(content_hash) = 64", name="ck_order_quarantine_hash"),
    )


def downgrade():
    op.drop_table("payment_order_reconciliation_quarantine")
    op.drop_index("ix_payment_order_reconciliation_evidence_payment_order_id", table_name="payment_order_reconciliation_evidence")
    op.drop_table("payment_order_reconciliation_evidence")
    op.drop_table("payment_order_reconciliation_attempts")
    op.drop_index("ix_payment_order_reconciliation_work_next_attempt_at", table_name="payment_order_reconciliation_work")
    op.drop_table("payment_order_reconciliation_work")
