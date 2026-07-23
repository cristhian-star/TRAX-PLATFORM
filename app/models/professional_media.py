from datetime import datetime

from app import db


class ProfessionalMedia(db.Model):
    __tablename__ = "professional_media"

    TYPE_AVATAR = "AVATAR"
    TYPE_COVER = "COVER"
    TYPE_GALLERY = "GALLERY"
    TYPES = (TYPE_AVATAR, TYPE_COVER, TYPE_GALLERY)

    STATUS_DRAFT = "BORRADOR"
    STATUS_PENDING = "PENDIENTE_MODERACION"
    STATUS_PUBLISHED = "PUBLICADO"
    STATUS_REJECTED = "RECHAZADO"
    STATUS_HIDDEN = "OCULTO"
    STATUS_DELETED = "ELIMINADO"
    STATUSES = (
        STATUS_DRAFT,
        STATUS_PENDING,
        STATUS_PUBLISHED,
        STATUS_REJECTED,
        STATUS_HIDDEN,
        STATUS_DELETED,
    )

    PROVIDER_LOCAL = "local"
    PROVIDER_CLOUDINARY = "cloudinary"

    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False, index=True)
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    media_type = db.Column(db.String(20), nullable=False, index=True)
    provider = db.Column(db.String(40), nullable=False)
    storage_key = db.Column(db.String(255), nullable=False, unique=True)
    public_url = db.Column(db.Text, nullable=False)
    secure_url = db.Column(db.Text)
    thumbnail_url = db.Column(db.Text)
    original_filename = db.Column(db.String(255))
    content_type = db.Column(db.String(80), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    checksum_sha256 = db.Column(db.String(64), nullable=False, index=True)
    title = db.Column(db.String(140))
    description = db.Column(db.Text)
    alt_text = db.Column(db.String(180))
    category = db.Column(db.String(80), index=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_primary = db.Column(db.Boolean, nullable=False, default=False, index=True)
    status = db.Column(db.String(50), nullable=False, default=STATUS_PUBLISHED, index=True)
    moderation_reason = db.Column(db.Text)
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)

    professional = db.relationship("Professional", back_populates="media_items")
    uploaded_by = db.relationship("User", foreign_keys=[uploaded_by_user_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_user_id])


db.Index(
    "ix_professional_media_professional_type_status",
    ProfessionalMedia.professional_id,
    ProfessionalMedia.media_type,
    ProfessionalMedia.status,
)
db.Index(
    "ix_professional_media_professional_sort",
    ProfessionalMedia.professional_id,
    ProfessionalMedia.sort_order,
)
