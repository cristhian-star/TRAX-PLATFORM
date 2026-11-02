"""Private records, current follow-up and durable reminder history."""
from app import db


class WorkRecord(db.Model):
    __tablename__ = 'work_records'
    __table_args__ = (db.CheckConstraint('version >= 1', name='ck_work_record_version'),
                      db.Index('ix_work_record_owner_date', 'owner_user_id', 'work_date', 'id'))
    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    work_date = db.Column(db.Date, nullable=False)
    client_name = db.Column(db.String(160), nullable=False, default='')
    contact = db.Column(db.String(254), nullable=False, default='')
    location = db.Column(db.String(300), nullable=False, default='')
    notes = db.Column(db.Text, nullable=False)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract_requests.id', ondelete='RESTRICT'))
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    followup = db.relationship('WorkFollowup', uselist=False, back_populates='record')


class WorkFollowup(db.Model):
    __tablename__ = 'work_followups'
    record_id = db.Column(db.Integer, db.ForeignKey('work_records.id', ondelete='RESTRICT'), primary_key=True)
    enabled = db.Column(db.Boolean, nullable=False, default=False)
    reason = db.Column(db.String(300), nullable=False, default='')
    tentative_date = db.Column(db.Date)
    remind_self = db.Column(db.Boolean, nullable=False, default=False)
    remind_client = db.Column(db.Boolean, nullable=False, default=False)
    advance_days = db.Column(db.Integer, nullable=False, default=1)
    notice_time = db.Column(db.String(5), nullable=False, default='09:00')
    version = db.Column(db.Integer, nullable=False, default=1)
    record = db.relationship('WorkRecord', back_populates='followup')
    __table_args__ = (db.CheckConstraint('version >= 1', name='ck_work_followup_version'),
                      db.CheckConstraint('advance_days IN (0,1,7)', name='ck_work_followup_advance'))


class WorkReminder(db.Model):
    __tablename__ = 'work_reminders'
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('work_records.id', ondelete='RESTRICT'), nullable=False, index=True)
    followup_version = db.Column(db.Integer, nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    audience = db.Column(db.String(10), nullable=False)
    due_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(12), nullable=False, default='PENDING')
    processed_at = db.Column(db.DateTime)
    notification_id = db.Column(db.Integer, db.ForeignKey('activity_notifications.id', ondelete='RESTRICT'))
    __table_args__ = (
        db.UniqueConstraint('record_id','followup_version','audience',name='uq_work_reminder_generation'),
        db.CheckConstraint("status IN ('PENDING','SENT','CANCELLED','SKIPPED')",name='ck_work_reminder_status'),
        db.CheckConstraint("audience IN ('SELF','CLIENT')",name='ck_work_reminder_audience'),
        db.Index('ix_work_reminder_due','status','due_at'))
