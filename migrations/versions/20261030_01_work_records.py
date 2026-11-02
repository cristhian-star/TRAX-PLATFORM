"""Private work records and reminders.

Revision ID: 20261030_01
Revises: 20261028_01
"""
from alembic import op
import sqlalchemy as sa
revision = '20261030_01'
down_revision = '20261028_01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('work_records',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('owner_user_id',sa.Integer(),sa.ForeignKey('users.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('title',sa.String(160),nullable=False),sa.Column('work_date',sa.Date(),nullable=False),
        sa.Column('client_name',sa.String(160),nullable=False),sa.Column('contact',sa.String(254),nullable=False),
        sa.Column('location',sa.String(300),nullable=False),sa.Column('notes',sa.Text(),nullable=False),
        sa.Column('contract_id',sa.Integer(),sa.ForeignKey('contract_requests.id',ondelete='RESTRICT')),
        sa.Column('version',sa.Integer(),nullable=False),sa.Column('created_at',sa.DateTime(),nullable=False),
        sa.Column('updated_at',sa.DateTime(),nullable=False),sa.CheckConstraint('version >= 1',name='ck_work_record_version'))
    op.create_index('ix_work_record_owner_date','work_records',['owner_user_id','work_date','id'])
    op.create_table('work_followups',
        sa.Column('record_id',sa.Integer(),sa.ForeignKey('work_records.id',ondelete='RESTRICT'),primary_key=True),
        sa.Column('enabled',sa.Boolean(),nullable=False),sa.Column('reason',sa.String(300),nullable=False),
        sa.Column('tentative_date',sa.Date()),sa.Column('remind_self',sa.Boolean(),nullable=False),
        sa.Column('remind_client',sa.Boolean(),nullable=False),sa.Column('advance_days',sa.Integer(),nullable=False),
        sa.Column('notice_time',sa.String(5),nullable=False),sa.Column('version',sa.Integer(),nullable=False),
        sa.CheckConstraint('version >= 1',name='ck_work_followup_version'),
        sa.CheckConstraint('advance_days IN (0,1,7)',name='ck_work_followup_advance'))
    op.create_table('work_reminders',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('record_id',sa.Integer(),sa.ForeignKey('work_records.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('followup_version',sa.Integer(),nullable=False),
        sa.Column('recipient_id',sa.Integer(),sa.ForeignKey('users.id',ondelete='RESTRICT'),nullable=False),
        sa.Column('audience',sa.String(10),nullable=False),sa.Column('due_at',sa.DateTime(),nullable=False),
        sa.Column('status',sa.String(12),nullable=False),sa.Column('processed_at',sa.DateTime()),
        sa.Column('notification_id',sa.Integer(),sa.ForeignKey('activity_notifications.id',ondelete='RESTRICT')),
        sa.UniqueConstraint('record_id','followup_version','audience',name='uq_work_reminder_generation'),
        sa.CheckConstraint("status IN ('PENDING','SENT','CANCELLED','SKIPPED')",name='ck_work_reminder_status'),
        sa.CheckConstraint("audience IN ('SELF','CLIENT')",name='ck_work_reminder_audience'))
    op.create_index('ix_work_reminders_record_id','work_reminders',['record_id'])
    op.create_index('ix_work_reminder_due','work_reminders',['status','due_at'])


def downgrade():
    # Deletes private record, follow-up and reminder history added by this increment.
    op.drop_table('work_reminders')
    op.drop_table('work_followups')
    op.drop_table('work_records')
