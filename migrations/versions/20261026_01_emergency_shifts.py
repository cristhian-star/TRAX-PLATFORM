"""Persist fixed emergency shifts and durable internal reminders."""
from alembic import op
import sqlalchemy as sa

revision = '20261026_01'
down_revision = '20260917_03'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('emergency_shifts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('professional_id', sa.Integer(), sa.ForeignKey('professionals.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('kind', sa.String(30), nullable=False),
        sa.Column('starts_at', sa.DateTime(), nullable=False),
        sa.Column('ends_at', sa.DateTime(), nullable=False),
        sa.Column('cutoff_at', sa.DateTime(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=False),
        sa.Column('commitment_version', sa.String(80), nullable=False),
        sa.Column('invalidated_at', sa.DateTime()),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.UniqueConstraint('professional_id','day','kind',name='uq_emergency_shift_block'),
        sa.CheckConstraint("kind IN ('GUARDIA_DIURNA','GUARDIA_NOCTURNA')",name='ck_emergency_shift_kind'),
        sa.CheckConstraint('ends_at > starts_at AND accepted_at <= cutoff_at AND cutoff_at < starts_at',name='ck_emergency_shift_times'),
        sa.CheckConstraint('version >= 1',name='ck_emergency_shift_version'))
    op.create_index('ix_emergency_shifts_professional_id','emergency_shifts',['professional_id'])
    op.create_table('emergency_shift_reminders',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('shift_id',sa.Integer(),sa.ForeignKey('emergency_shifts.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('kind',sa.String(20),nullable=False),
        sa.Column('due_at',sa.DateTime(),nullable=False),
        sa.Column('status',sa.String(10),nullable=False),
        sa.Column('processed_at',sa.DateTime()),
        sa.UniqueConstraint('shift_id','kind',name='uq_emergency_shift_reminder'),
        sa.CheckConstraint("kind IN ('T_MINUS_6H','T_MINUS_1H')",name='ck_emergency_reminder_kind'),
        sa.CheckConstraint("status IN ('PENDING','SENT','SKIPPED')",name='ck_emergency_reminder_status'))
    op.create_index('ix_emergency_shift_reminders_due_at','emergency_shift_reminders',['due_at'])


def downgrade():
    # Explicitly destructive for these new tables; never run against live reservations.
    op.drop_table('emergency_shift_reminders')
    op.drop_table('emergency_shifts')
