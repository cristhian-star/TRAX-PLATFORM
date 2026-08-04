from datetime import datetime

from app import db


class Review(db.Model):
    __tablename__ = "reviews"
    __table_args__ = (
        db.UniqueConstraint("contract_id", name="uq_reviews_contract_id"),
        db.CheckConstraint(
            "origin IS NULL OR origin IN ('CONTRACTUAL', 'LEGACY')",
            name="ck_reviews_origin",
        ),
        db.CheckConstraint(
            "verification_status IS NULL OR verification_status IN "
            "('VERIFIED', 'UNVERIFIED')",
            name="ck_reviews_verification_status",
        ),
        db.CheckConstraint(
            "comment_visibility_status IS NULL OR "
            "comment_visibility_status IN "
            "('VISIBLE', 'PENDING_MODERATION', 'HIDDEN', 'REDACTED')",
            name="ck_reviews_comment_visibility_status",
        ),
        db.CheckConstraint(
            "rating_eligibility_status IS NULL OR "
            "rating_eligibility_status IN ('ELIGIBLE', 'EXCLUDED')",
            name="ck_reviews_rating_eligibility_status",
        ),
        db.CheckConstraint(
            "origin <> 'CONTRACTUAL' OR (contract_id IS NOT NULL AND "
            "verification_status = 'VERIFIED' AND rating BETWEEN 1 AND 5 "
            "AND correlation_id IS NOT NULL AND payload_hash IS NOT NULL)",
            name="ck_reviews_contractual_integrity",
        ),
        db.CheckConstraint(
            "rating_eligibility_status <> 'ELIGIBLE' OR ("
            "verification_status = 'VERIFIED' AND contract_id IS NOT NULL "
            "AND rating BETWEEN 1 AND 5)",
            name="ck_reviews_rating_eligible_integrity",
        ),
    )

    ESTADOS = (
        "VISIBLE",
        "OCULTA",
        "REPORTADA",
    )

    ORIGIN_CONTRACTUAL = "CONTRACTUAL"
    ORIGIN_LEGACY = "LEGACY"
    ORIGINS = (ORIGIN_CONTRACTUAL, ORIGIN_LEGACY)

    VERIFICATION_VERIFIED = "VERIFIED"
    VERIFICATION_UNVERIFIED = "UNVERIFIED"
    VERIFICATION_STATUSES = (
        VERIFICATION_VERIFIED,
        VERIFICATION_UNVERIFIED,
    )

    COMMENT_VISIBLE = "VISIBLE"
    COMMENT_PENDING_MODERATION = "PENDING_MODERATION"
    COMMENT_HIDDEN = "HIDDEN"
    COMMENT_REDACTED = "REDACTED"
    COMMENT_VISIBILITY_STATUSES = (
        COMMENT_VISIBLE,
        COMMENT_PENDING_MODERATION,
        COMMENT_HIDDEN,
        COMMENT_REDACTED,
    )

    RATING_ELIGIBLE = "ELIGIBLE"
    RATING_EXCLUDED = "EXCLUDED"
    RATING_ELIGIBILITY_STATUSES = (
        RATING_ELIGIBLE,
        RATING_EXCLUDED,
    )

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(
        db.Integer,
        db.ForeignKey("contract_requests.id"),
        nullable=True,
        index=True,
    )
    cliente_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    comentario = db.Column(db.Text)
    comment_public = db.Column(db.Text)
    origin = db.Column(db.String(20), nullable=True)
    verification_status = db.Column(db.String(20), nullable=True)
    comment_visibility_status = db.Column(db.String(30), nullable=True)
    rating_eligibility_status = db.Column(db.String(20), nullable=True)
    correlation_id = db.Column(db.String(36), nullable=True, index=True)
    payload_hash = db.Column(db.String(64), nullable=True)
    legacy_metadata_json = db.Column(db.JSON)
    moderated_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
    )
    moderated_at = db.Column(db.DateTime)
    moderation_reason = db.Column(db.String(255))
    estado = db.Column(db.String(50), nullable=False, default="VISIBLE")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    contract = db.relationship("ContractRequest")
    moderator = db.relationship("User", foreign_keys=[moderated_by_user_id])
