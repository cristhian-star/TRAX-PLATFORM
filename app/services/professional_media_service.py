from datetime import datetime

from flask import current_app

from app import db
from app.models.audit_log import AuditLog
from app.models.professional import Professional
from app.models.professional_media import ProfessionalMedia
from app.services.media_image_service import process_uploaded_image
from app.services.media_storage_service import get_media_storage


MAX_GALLERY_IMAGES = 12
ACTIVE_STATUSES = (
    ProfessionalMedia.STATUS_DRAFT,
    ProfessionalMedia.STATUS_PENDING,
    ProfessionalMedia.STATUS_PUBLISHED,
    ProfessionalMedia.STATUS_REJECTED,
    ProfessionalMedia.STATUS_HIDDEN,
)


def _clean_text(value, max_length):
    value = (value or "").strip()
    if not value:
        return None
    if len(value) > max_length:
        raise ValueError("Texto demasiado largo")

    return value


def _get_professional_for_user(user_id):
    professional = Professional.query.filter_by(user_id=user_id).first()
    if professional is None:
        raise PermissionError("Perfil profesional no encontrado")

    return professional


def _get_owned_media(media_id, user_id):
    media = db.session.get(ProfessionalMedia, media_id)
    if media is None or media.deleted_at is not None:
        raise ValueError("Imagen no encontrada")
    if media.professional.user_id != user_id:
        raise PermissionError("No autorizado")

    return media


def _initial_status():
    if current_app.config.get("MEDIA_AUTO_PUBLISH", True):
        return ProfessionalMedia.STATUS_PUBLISHED

    return ProfessionalMedia.STATUS_PENDING


def _next_sort_order(professional_id):
    current = (
        db.session.query(db.func.max(ProfessionalMedia.sort_order))
        .filter(
            ProfessionalMedia.professional_id == professional_id,
            ProfessionalMedia.media_type == ProfessionalMedia.TYPE_GALLERY,
            ProfessionalMedia.deleted_at.is_(None),
            ProfessionalMedia.status != ProfessionalMedia.STATUS_DELETED,
        )
        .scalar()
    )
    return (current or 0) + 1


def _active_count(professional_id, media_type):
    return (
        ProfessionalMedia.query
        .filter(
            ProfessionalMedia.professional_id == professional_id,
            ProfessionalMedia.media_type == media_type,
            ProfessionalMedia.deleted_at.is_(None),
            ProfessionalMedia.status != ProfessionalMedia.STATUS_DELETED,
        )
        .count()
    )


def _soft_delete_existing_identity(professional_id, media_type):
    now = datetime.utcnow()
    existing_items = (
        ProfessionalMedia.query
        .filter(
            ProfessionalMedia.professional_id == professional_id,
            ProfessionalMedia.media_type == media_type,
            ProfessionalMedia.deleted_at.is_(None),
            ProfessionalMedia.status != ProfessionalMedia.STATUS_DELETED,
        )
        .all()
    )
    for item in existing_items:
        item.status = ProfessionalMedia.STATUS_DELETED
        item.deleted_at = now
        item.is_primary = False


def _audit(actor_user_id, professional, action, media=None, description=""):
    db.session.add(AuditLog(
        actor_user_id=actor_user_id,
        target_user_id=professional.user_id,
        action=action,
        description=description or f"Media profesional {media.id if media else ''}".strip(),
    ))


def upload_professional_media(
    user_id,
    file_storage,
    media_type,
    title=None,
    description=None,
    alt_text=None,
    category=None,
    storage=None,
):
    if media_type not in ProfessionalMedia.TYPES:
        raise ValueError("Tipo de imagen invalido")

    professional = _get_professional_for_user(user_id)
    if media_type == ProfessionalMedia.TYPE_GALLERY and _active_count(professional.id, media_type) >= MAX_GALLERY_IMAGES:
        raise ValueError("La galeria alcanzo el maximo de imagenes permitidas")

    processed_image = process_uploaded_image(file_storage)
    storage = storage or get_media_storage()
    stored_image = storage.upload_image(processed_image, media_type)

    try:
        if media_type in (ProfessionalMedia.TYPE_AVATAR, ProfessionalMedia.TYPE_COVER):
            _soft_delete_existing_identity(professional.id, media_type)

        media = ProfessionalMedia(
            professional_id=professional.id,
            uploaded_by_user_id=user_id,
            media_type=media_type,
            provider=stored_image.provider,
            storage_key=stored_image.storage_key,
            public_url=stored_image.public_url,
            secure_url=stored_image.secure_url,
            thumbnail_url=stored_image.thumbnail_url,
            original_filename=_clean_text(file_storage.filename, 255),
            content_type=processed_image.content_type,
            file_size_bytes=processed_image.file_size_bytes,
            width=processed_image.width,
            height=processed_image.height,
            checksum_sha256=processed_image.checksum_sha256,
            title=_clean_text(title, 140),
            description=_clean_text(description, 1000),
            alt_text=_clean_text(alt_text, 180),
            category=_clean_text(category, 80),
            sort_order=0 if media_type != ProfessionalMedia.TYPE_GALLERY else _next_sort_order(professional.id),
            is_primary=media_type in (ProfessionalMedia.TYPE_AVATAR, ProfessionalMedia.TYPE_COVER),
            status=_initial_status(),
        )
        db.session.add(media)
        db.session.flush()
        _audit(user_id, professional, "PROFESSIONAL_MEDIA_UPLOADED", media, f"{media_type} subida.")
        db.session.commit()
    except Exception:
        db.session.rollback()
        try:
            storage.delete_image(stored_image.storage_key)
        except Exception:
            current_app.logger.error("No se pudo limpiar un asset externo tras rollback")
        raise

    return media


def update_professional_media_metadata(user_id, media_id, title=None, description=None, alt_text=None, category=None):
    media = _get_owned_media(media_id, user_id)
    media.title = _clean_text(title, 140)
    media.description = _clean_text(description, 1000)
    media.alt_text = _clean_text(alt_text, 180)
    media.category = _clean_text(category, 80)
    _audit(user_id, media.professional, "PROFESSIONAL_MEDIA_METADATA_UPDATED", media)
    db.session.commit()
    return media


def reorder_professional_gallery(user_id, ordered_ids):
    professional = _get_professional_for_user(user_id)
    unique_ordered_ids = list(dict.fromkeys(ordered_ids))
    media_items = (
        ProfessionalMedia.query
        .filter(
            ProfessionalMedia.professional_id == professional.id,
            ProfessionalMedia.media_type == ProfessionalMedia.TYPE_GALLERY,
            ProfessionalMedia.id.in_(unique_ordered_ids),
            ProfessionalMedia.deleted_at.is_(None),
        )
        .all()
    )
    by_id = {item.id: item for item in media_items}
    if len(by_id) != len(unique_ordered_ids):
        raise PermissionError("No autorizado")

    for index, media_id in enumerate(unique_ordered_ids, start=1):
        by_id[media_id].sort_order = index

    _audit(user_id, professional, "PROFESSIONAL_MEDIA_REORDERED", description="Galeria reordenada.")
    db.session.commit()
    return list(by_id.values())


def set_gallery_primary(user_id, media_id):
    media = _get_owned_media(media_id, user_id)
    if media.media_type != ProfessionalMedia.TYPE_GALLERY:
        raise ValueError("Solo una imagen de galeria puede marcarse como principal")

    ProfessionalMedia.query.filter_by(
        professional_id=media.professional_id,
        media_type=ProfessionalMedia.TYPE_GALLERY,
    ).update({"is_primary": False})
    media.is_primary = True
    _audit(user_id, media.professional, "PROFESSIONAL_MEDIA_PRIMARY_SET", media)
    db.session.commit()
    return media


def soft_delete_professional_media(user_id, media_id):
    media = _get_owned_media(media_id, user_id)
    media.status = ProfessionalMedia.STATUS_DELETED
    media.deleted_at = datetime.utcnow()
    media.is_primary = False
    _audit(user_id, media.professional, "PROFESSIONAL_MEDIA_DELETED", media)
    db.session.commit()
    return media


def get_pending_media():
    return (
        ProfessionalMedia.query
        .filter(
            ProfessionalMedia.status.in_((
                ProfessionalMedia.STATUS_PENDING,
                ProfessionalMedia.STATUS_REJECTED,
                ProfessionalMedia.STATUS_HIDDEN,
            )),
            ProfessionalMedia.deleted_at.is_(None),
        )
        .order_by(ProfessionalMedia.created_at.asc(), ProfessionalMedia.id.asc())
        .all()
    )


def moderate_professional_media(media_id, status, admin_user_id, reason=None):
    if status not in (
        ProfessionalMedia.STATUS_PUBLISHED,
        ProfessionalMedia.STATUS_REJECTED,
        ProfessionalMedia.STATUS_HIDDEN,
        ProfessionalMedia.STATUS_PENDING,
    ):
        raise ValueError("Estado de moderacion invalido")

    media = db.session.get(ProfessionalMedia, media_id)
    if media is None or media.status == ProfessionalMedia.STATUS_DELETED:
        return None

    media.status = status
    media.moderation_reason = _clean_text(reason, 1000)
    media.reviewed_by_user_id = admin_user_id
    media.reviewed_at = datetime.utcnow()
    _audit(admin_user_id, media.professional, f"PROFESSIONAL_MEDIA_{status}", media, media.moderation_reason or "")
    db.session.commit()
    return media


def _published_media_query(professional_id, media_type=None):
    query = ProfessionalMedia.query.filter(
        ProfessionalMedia.professional_id == professional_id,
        ProfessionalMedia.status == ProfessionalMedia.STATUS_PUBLISHED,
        ProfessionalMedia.deleted_at.is_(None),
    )
    if media_type:
        query = query.filter_by(media_type=media_type)

    return query


def get_published_identity_media(professional):
    if professional is None:
        return {"avatar": None, "cover": None, "gallery": []}

    avatar = (
        _published_media_query(professional.id, ProfessionalMedia.TYPE_AVATAR)
        .order_by(ProfessionalMedia.created_at.desc(), ProfessionalMedia.id.desc())
        .first()
    )
    cover = (
        _published_media_query(professional.id, ProfessionalMedia.TYPE_COVER)
        .order_by(ProfessionalMedia.created_at.desc(), ProfessionalMedia.id.desc())
        .first()
    )
    gallery = (
        _published_media_query(professional.id, ProfessionalMedia.TYPE_GALLERY)
        .order_by(ProfessionalMedia.is_primary.desc(), ProfessionalMedia.sort_order.asc(), ProfessionalMedia.id.asc())
        .limit(MAX_GALLERY_IMAGES)
        .all()
    )
    return {"avatar": avatar, "cover": cover, "gallery": gallery}


def get_private_media_items(professional):
    if professional is None:
        return []

    return (
        ProfessionalMedia.query
        .filter(
            ProfessionalMedia.professional_id == professional.id,
            ProfessionalMedia.deleted_at.is_(None),
            ProfessionalMedia.status != ProfessionalMedia.STATUS_DELETED,
        )
        .order_by(ProfessionalMedia.media_type.asc(), ProfessionalMedia.sort_order.asc(), ProfessionalMedia.id.asc())
        .all()
    )


def build_professional_media_context(professional):
    published = get_published_identity_media(professional)
    gallery_items = published["gallery"]
    avatar = published["avatar"]
    cover = published["cover"]

    return {
        "avatar_url": avatar.thumbnail_url if avatar else getattr(professional, "logo_url", None),
        "avatar_alt": avatar.alt_text if avatar and avatar.alt_text else f"Avatar de {getattr(professional, 'nombre', 'profesional')}",
        "cover_url": cover.secure_url if cover else getattr(professional, "cover_url", None),
        "cover_alt": cover.alt_text if cover and cover.alt_text else "",
        "gallery": gallery_items,
        "has_media_gallery": bool(gallery_items),
    }


def get_professionals_avatar_context(professionals):
    professional_ids = [professional.id for professional in professionals if getattr(professional, "id", None)]
    if not professional_ids:
        return {}

    avatars = (
        ProfessionalMedia.query
        .filter(
            ProfessionalMedia.professional_id.in_(professional_ids),
            ProfessionalMedia.media_type == ProfessionalMedia.TYPE_AVATAR,
            ProfessionalMedia.status == ProfessionalMedia.STATUS_PUBLISHED,
            ProfessionalMedia.deleted_at.is_(None),
        )
        .order_by(ProfessionalMedia.professional_id.asc(), ProfessionalMedia.created_at.desc())
        .all()
    )
    by_professional_id = {}
    for avatar in avatars:
        by_professional_id.setdefault(avatar.professional_id, avatar)

    return {
        professional.id: {
            "avatar_url": by_professional_id[professional.id].thumbnail_url
            if professional.id in by_professional_id
            else professional.logo_url,
            "avatar_alt": f"Avatar de {professional.nombre}",
        }
        for professional in professionals
    }
