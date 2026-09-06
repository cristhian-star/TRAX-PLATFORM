import unicodedata
from datetime import datetime, timezone

from app import db
from app.models.audit_log import AuditLog
from app.models.contract_request import ContractRequest
from app.models.review import Review
from app.services.actor_policy_service import require_active_actor


REASON_NOT_CONTRACTUAL = "NOT_CONTRACTUAL"
REASON_DUPLICATE = "DUPLICATE"
REASON_FRAUD_CONFIRMED = "FRAUD_CONFIRMED"
REASON_DATA_CORRUPTION = "DATA_CORRUPTION"
REASON_PERSONAL_DATA = "PERSONAL_DATA"
REASON_OFFENSIVE_CONTENT = "OFFENSIVE_CONTENT"
MODERATION_REASONS = frozenset((
    REASON_NOT_CONTRACTUAL,
    REASON_DUPLICATE,
    REASON_FRAUD_CONFIRMED,
    REASON_DATA_CORRUPTION,
    REASON_PERSONAL_DATA,
    REASON_OFFENSIVE_CONTENT,
))

ACTION_SHOW = "SHOW"
ACTION_HIDE = "HIDE"
ACTION_REDACT = "REDACT"
COMMENT_ACTIONS = frozenset((ACTION_SHOW, ACTION_HIDE, ACTION_REDACT))


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _lock_review(review_id):
    review = Review.query.filter_by(id=review_id).with_for_update().first()
    if review is None:
        raise LookupError("Review no encontrada")
    if review.contract_id is None:
        raise ValueError("La moderacion contractual requiere un contrato")
    contract = db.session.get(ContractRequest, review.contract_id)
    if contract is None:
        raise ValueError("Contrato de la review inexistente")
    return review, contract


def _require_reason(reason):
    if reason not in MODERATION_REASONS:
        raise ValueError("Motivo de moderacion invalido")
    return reason


def _normalize_redacted_comment(comment):
    if not isinstance(comment, str):
        raise ValueError("Comentario redactado requerido")
    normalized = unicodedata.normalize("NFKC", comment)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise ValueError("Comentario redactado requerido")
    return normalized


def _add_audit(actor, contract, review, action, reason, metadata=None):
    audit = AuditLog(
        actor_user_id=actor.id,
        target_user_id=contract.professional_user_id,
        action=action,
        description=f"Moderacion de review contractual #{review.id}.",
        entity_type="Review",
        entity_id=review.id,
        contract_id=contract.id,
        correlation_id=review.correlation_id,
        operation=action,
        metadata_json={"reason": reason, **(metadata or {})},
    )
    db.session.add(audit)
    db.session.flush()


def report_contract_review(review_id, *, actor_user_id):
    try:
        actor = require_active_actor(actor_user_id, ("CLIENTE", "PROFESIONAL"))
        review, contract = _lock_review(review_id)
        if actor.id not in (contract.cliente_id, contract.professional_user_id):
            raise PermissionError("Solo las partes del contrato pueden reportar")
        if actor.rol == "CLIENTE" and actor.id != contract.cliente_id:
            raise PermissionError("Identidad de parte incoherente")
        if actor.rol == "PROFESIONAL" and actor.id != contract.professional_user_id:
            raise PermissionError("Identidad de parte incoherente")
        if review.comment_visibility_status == Review.COMMENT_PENDING_MODERATION:
            db.session.rollback()
            return review
        review.comment_visibility_status = Review.COMMENT_PENDING_MODERATION
        _add_audit(actor, contract, review, "CONTRACT_REVIEW_REPORTED", "REPORTED")
        db.session.commit()
        return review
    except Exception:
        db.session.rollback()
        raise


def moderate_contract_review_comment(
    review_id,
    *,
    actor_user_id,
    action,
    reason,
    redacted_comment=None,
):
    try:
        actor = require_active_actor(actor_user_id, ("SUPER_ADMIN",))
        if action not in COMMENT_ACTIONS:
            raise ValueError("Accion de moderacion invalida")
        reason = _require_reason(reason)
        review, contract = _lock_review(review_id)
        if action == ACTION_SHOW:
            review.comment_visibility_status = Review.COMMENT_VISIBLE
        elif action == ACTION_HIDE:
            review.comment_visibility_status = Review.COMMENT_HIDDEN
        else:
            review.comment_public = _normalize_redacted_comment(redacted_comment)
            review.comment_visibility_status = Review.COMMENT_REDACTED
        review.moderated_by_user_id = actor.id
        review.moderated_at = _utcnow()
        review.moderation_reason = reason
        _add_audit(
            actor,
            contract,
            review,
            "CONTRACT_REVIEW_COMMENT_MODERATED",
            reason,
            {"comment_action": action},
        )
        db.session.commit()
        return review
    except Exception:
        db.session.rollback()
        raise


def exclude_contract_review_rating(review_id, *, actor_user_id, reason):
    try:
        actor = require_active_actor(actor_user_id, ("SUPER_ADMIN",))
        reason = _require_reason(reason)
        review, contract = _lock_review(review_id)
        review.rating_eligibility_status = Review.RATING_EXCLUDED
        review.moderated_by_user_id = actor.id
        review.moderated_at = _utcnow()
        review.moderation_reason = reason
        _add_audit(
            actor,
            contract,
            review,
            "CONTRACT_REVIEW_RATING_EXCLUDED",
            reason,
        )
        db.session.commit()
        return review
    except Exception:
        db.session.rollback()
        raise


def get_pending_contract_review_moderation(*, actor_user_id):
    require_active_actor(actor_user_id, ("SUPER_ADMIN",))
    return Review.query.filter_by(
        comment_visibility_status=Review.COMMENT_PENDING_MODERATION
    ).order_by(Review.created_at.asc(), Review.id.asc()).all()


__all__ = (
    "ACTION_HIDE",
    "ACTION_REDACT",
    "ACTION_SHOW",
    "MODERATION_REASONS",
    "exclude_contract_review_rating",
    "get_pending_contract_review_moderation",
    "moderate_contract_review_comment",
    "report_contract_review",
)
