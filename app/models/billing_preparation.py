"""Internal declared data. No authorized fiscal documents are stored here."""
from app import db


class BillingProfile(db.Model):
    __tablename__ = "billing_profiles"
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True)
    cuit = db.Column(db.String(11), nullable=False)
    legal_name = db.Column(db.String(200), nullable=False)
    fiscal_address = db.Column(db.String(300), nullable=False)
    verification_status = db.Column(db.String(24), nullable=False, default="DECLARED_UNVERIFIED")
    version = db.Column(db.Integer, nullable=False, default=1)
    __table_args__ = (
        db.CheckConstraint("verification_status = 'DECLARED_UNVERIFIED'", name="ck_billing_profile_declared"),
        db.CheckConstraint("version >= 1", name="ck_billing_profile_version"),
    )
    __mapper_args__ = {"version_id_col": version}


class BillingDraft(db.Model):
    __tablename__ = "billing_drafts"
    id = db.Column(db.Integer, primary_key=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("billing_profiles.owner_user_id", ondelete="RESTRICT"), nullable=False)
    request_key = db.Column(db.String(36), nullable=False)
    profile_version = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    recipient_name = db.Column(db.String(200), nullable=False)
    service_from = db.Column(db.Date, nullable=False)
    service_to = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="INTERNAL_DRAFT")
    __table_args__ = (
        db.UniqueConstraint("owner_user_id", "request_key", name="uq_billing_draft_request"),
        db.CheckConstraint("status = 'INTERNAL_DRAFT'", name="ck_billing_draft_internal"),
        db.CheckConstraint("amount > 0 AND amount <= 999999999999.99", name="ck_billing_draft_amount"),
        db.CheckConstraint("service_from <= service_to", name="ck_billing_draft_period"),
        db.CheckConstraint("profile_version >= 1", name="ck_billing_draft_profile_version"),
    )
