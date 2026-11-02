"""Persisted fixed blocks. Timestamps are naive UTC, matching the existing ledger."""
from app import db


class EmergencyShift(db.Model):
    __tablename__ = 'emergency_shifts'
    __table_args__ = (
        db.UniqueConstraint('professional_id', 'day', 'kind', name='uq_emergency_shift_block'),
        db.CheckConstraint("kind IN ('GUARDIA_DIURNA','GUARDIA_NOCTURNA')", name='ck_emergency_shift_kind'),
        db.CheckConstraint('ends_at > starts_at AND accepted_at <= cutoff_at AND cutoff_at < starts_at', name='ck_emergency_shift_times'),
        db.CheckConstraint('version >= 1', name='ck_emergency_shift_version'),
    )
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id', ondelete='RESTRICT'), nullable=False, index=True)
    day = db.Column(db.Date, nullable=False)
    kind = db.Column(db.String(30), nullable=False)
    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=False)
    cutoff_at = db.Column(db.DateTime, nullable=False)
    accepted_at = db.Column(db.DateTime, nullable=False)
    commitment_version = db.Column(db.String(80), nullable=False)
    invalidated_at = db.Column(db.DateTime)
    version = db.Column(db.Integer, nullable=False, default=1)


class EmergencyShiftReminder(db.Model):
    __tablename__ = 'emergency_shift_reminders'
    __table_args__ = (
        db.UniqueConstraint('shift_id', 'kind', name='uq_emergency_shift_reminder'),
        db.CheckConstraint("kind IN ('T_MINUS_6H','T_MINUS_1H')", name='ck_emergency_reminder_kind'),
        db.CheckConstraint("status IN ('PENDING','SENT','SKIPPED')", name='ck_emergency_reminder_status'),
    )
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('emergency_shifts.id', ondelete='RESTRICT'), nullable=False)
    kind = db.Column(db.String(20), nullable=False)
    due_at = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(10), nullable=False, default='PENDING')
    processed_at = db.Column(db.DateTime)
