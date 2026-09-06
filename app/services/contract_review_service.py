import hashlib
import json
import unicodedata
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from app import db
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.contract_request import ContractRequest
from app.models.operation_command import OperationCommand
from app.models.professional import Professional
from app.models.reputation_event import ReputationEvent
from app.models.review import Review
from app.services.actor_policy_service import require_active_actor
from app.services.contract_service import require_idempotency_key
from app.services.notification_service import (
    CATEGORIA_CONTRATACIONES,
    PRIORIDAD_INFO,
)


OPERATION_CREATE_CONTRACT_REVIEW = "CREATE_CONTRACT_REVIEW"
RESULT_ENTITY_REVIEW = "Review"
NOTIFICATION_TEMPLATE_REVIEW_RECEIVED = "CONTRACT_REVIEW_RECEIVED"


class ContractReviewConflictError(ValueError):
    """The requested review conflicts with an existing command or review."""


class ContractReviewIdempotencyConflictError(ContractReviewConflictError):
    """An idempotency key was reused for a different review payload."""


class ContractReviewIntegrityError(RuntimeError):
    """Persisted command or result data is missing or incoherent."""


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalize_comment(comment):
    if comment is None:
        return None
    if not isinstance(comment, str):
        raise ValueError("Comentario invalido")
    normalized = unicodedata.normalize("NFKC", comment)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n").strip()
    return normalized or None


def _require_rating(rating):
    if not isinstance(rating, int) or isinstance(rating, bool):
        raise ValueError("Rating invalido")
    if rating not in (1, 2, 3, 4, 5):
        raise ValueError("Rating invalido")
    return rating


def _require_identifier(value, label):
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{label} invalido")
    return value


def _canonical_payload(contract_id, rating, comment):
    return {
        "schema_version": 1,
        "contract_id": int(contract_id),
        "rating": rating,
        "comment": comment,
    }


def _payload_hash(payload):
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _derived_key(prefix, *parts):
    digest = hashlib.sha256(
        ":".join(str(part) for part in parts).encode("utf-8")
    ).hexdigest()
    return f"{prefix}:{digest}"


def _normalize_correlation_id(correlation_id):
    if correlation_id is None:
        return str(uuid4())
    try:
        return str(UUID(str(correlation_id)))
    except (TypeError, ValueError, AttributeError):
        raise ValueError("Correlation id invalido") from None


def _lock_contract(contract_id):
    contract = (
        ContractRequest.query
        .filter_by(id=contract_id)
        .with_for_update()
        .first()
    )
    if contract is None:
        raise LookupError("Contratacion no encontrada")
    return contract


def _load_professional(professional_id):
    return db.session.get(Professional, professional_id)


def _require_contract_eligibility(contract, actor):
    if contract.cliente_id != actor.id:
        raise PermissionError(
            "Solo el cliente propietario puede crear la review contractual"
        )
    if contract.estado != "CONFIRMADA":
        raise ValueError("La contratacion debe estar CONFIRMADA")

    professional = _load_professional(contract.professional_id)
    if professional is None:
        raise ContractReviewIntegrityError("Perfil profesional inexistente")
    if professional.user_id is None:
        raise ContractReviewIntegrityError(
            "Perfil profesional sin usuario propietario"
        )
    if contract.professional_user_id != professional.user_id:
        raise ContractReviewIntegrityError(
            "Identidad profesional contractual incoherente"
        )
    return professional


def _find_command(actor_user_id, idempotency_key, lock=False):
    query = OperationCommand.query.filter_by(
        actor_user_id=actor_user_id,
        operation=OPERATION_CREATE_CONTRACT_REVIEW,
        idempotency_key=idempotency_key,
    )
    if lock:
        query = query.with_for_update()
    return query.first()


def _load_replay(command, contract, payload_hash):
    if command.payload_hash != payload_hash:
        raise ContractReviewIdempotencyConflictError(
            "La idempotency key ya fue usada con un payload diferente"
        )
    if command.status == OperationCommand.STATUS_PROCESSING:
        raise ContractReviewConflictError(
            "Comando de review en proceso; reintento permitido"
        )
    if command.status == OperationCommand.STATUS_FAILED:
        raise ContractReviewConflictError(
            f"El comando previo fallo: {command.failure_code or 'UNKNOWN'}"
        )
    if command.status != OperationCommand.STATUS_SUCCEEDED:
        raise ContractReviewIntegrityError("Estado de comando incoherente")
    if (
        command.result_entity_type != RESULT_ENTITY_REVIEW
        or command.result_entity_id is None
    ):
        raise ContractReviewIntegrityError(
            "El comando no referencia una review recuperable"
        )

    review = db.session.get(Review, command.result_entity_id)
    if review is None:
        raise ContractReviewIntegrityError(
            "La review idempotente ya no esta disponible"
        )
    if (
        review.contract_id != contract.id
        or review.cliente_id != contract.cliente_id
        or review.professional_id != contract.professional_id
        or review.payload_hash != command.payload_hash
        or review.correlation_id != command.correlation_id
        or review.origin != Review.ORIGIN_CONTRACTUAL
        or review.verification_status != Review.VERIFICATION_VERIFIED
    ):
        raise ContractReviewIntegrityError(
            "El resultado idempotente es incoherente con el contrato"
        )
    return review


def _begin_command(
    actor_user_id,
    idempotency_key,
    payload_hash,
    correlation_id,
    contract,
):
    existing = _find_command(actor_user_id, idempotency_key, lock=True)
    if existing is not None:
        return existing, _load_replay(existing, contract, payload_hash)

    command = OperationCommand(
        actor_user_id=actor_user_id,
        operation=OPERATION_CREATE_CONTRACT_REVIEW,
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
        status=OperationCommand.STATUS_PROCESSING,
        correlation_id=_normalize_correlation_id(correlation_id),
    )
    db.session.add(command)
    db.session.flush()
    return command, None


def _create_review(contract, command, rating, comment):
    review = Review(
        contract_id=contract.id,
        cliente_id=contract.cliente_id,
        professional_id=contract.professional_id,
        rating=rating,
        comentario=comment,
        comment_public=comment,
        origin=Review.ORIGIN_CONTRACTUAL,
        verification_status=Review.VERIFICATION_VERIFIED,
        comment_visibility_status=Review.COMMENT_VISIBLE,
        rating_eligibility_status=Review.RATING_ELIGIBLE,
        correlation_id=command.correlation_id,
        payload_hash=command.payload_hash,
        estado="VISIBLE",
    )
    db.session.add(review)
    db.session.flush()
    return review


def _create_reputation_event(contract, review, command):
    event = ReputationEvent(
        user_id=contract.professional_user_id,
        review_id=review.id,
        contract_id=contract.id,
        source_type=ReputationEvent.SOURCE_CONTRACT_REVIEW,
        event_type=ReputationEvent.EVENT_REVIEW_RECORDED,
        event_value=review.rating,
        origin=ReputationEvent.ORIGIN_CONTRACTUAL,
        correlation_id=command.correlation_id,
        tipo_evento=ReputationEvent.EVENT_REVIEW_RECORDED,
        puntos=None,
        descripcion="Review contractual verificada registrada",
    )
    db.session.add(event)
    db.session.flush()
    return event


def _create_audit_log(contract, review, command):
    audit = AuditLog(
        actor_user_id=contract.cliente_id,
        target_user_id=contract.professional_user_id,
        action="CONTRACT_REVIEW_CREATED",
        description=f"Review contractual creada para contratacion #{contract.id}.",
        entity_type=RESULT_ENTITY_REVIEW,
        entity_id=review.id,
        contract_id=contract.id,
        correlation_id=command.correlation_id,
        operation=command.operation,
        idempotency_key=command.idempotency_key,
        metadata_json={
            "rating": review.rating,
            "review_origin": review.origin,
            "verification_status": review.verification_status,
        },
    )
    db.session.add(audit)
    db.session.flush()
    return audit


def _create_notification(contract, review, command):
    notification = ActivityNotification(
        user_id=contract.professional_user_id,
        actor_user_id=contract.cliente_id,
        correlation_id=command.correlation_id,
        idempotency_key=_derived_key(
            "notification",
            command.actor_user_id,
            command.operation,
            command.idempotency_key,
            contract.professional_user_id,
        ),
        template_key=NOTIFICATION_TEMPLATE_REVIEW_RECEIVED,
        channel="INTERNAL",
        delivery_status="DELIVERED",
        attempt_count=0,
        tipo=NOTIFICATION_TEMPLATE_REVIEW_RECEIVED,
        categoria=CATEGORIA_CONTRATACIONES,
        titulo="Recibiste una review contractual",
        mensaje="Un cliente registro una valoracion sobre un contrato confirmado.",
        url_destino=f"/contratacion/{contract.id}",
        entity_type=RESULT_ENTITY_REVIEW,
        entity_id=review.id,
        prioridad=PRIORIDAD_INFO,
        requiere_accion=False,
    )
    db.session.add(notification)
    db.session.flush()
    return notification


def _complete_command(command, review):
    command.status = OperationCommand.STATUS_SUCCEEDED
    command.result_entity_type = RESULT_ENTITY_REVIEW
    command.result_entity_id = review.id
    command.completed_at = _utcnow()
    command.failure_code = None
    db.session.flush()


def _recover_integrity_race(
    actor_user_id,
    contract_id,
    idempotency_key,
    payload_hash,
):
    actor = require_active_actor(actor_user_id, ("CLIENTE",))
    contract = _lock_contract(contract_id)
    _require_contract_eligibility(contract, actor)
    existing = _find_command(actor_user_id, idempotency_key, lock=True)
    if existing is None:
        db.session.rollback()
        return None
    review = _load_replay(existing, contract, payload_hash)
    db.session.rollback()
    return review


def create_contract_review(
    *,
    actor_user_id,
    contract_id,
    rating,
    comment,
    idempotency_key,
    correlation_id=None,
):
    idempotency_key = require_idempotency_key(idempotency_key)
    rating = _require_rating(rating)
    comment = _normalize_comment(comment)
    contract_id = _require_identifier(contract_id, "ID de contratacion")

    payload = _canonical_payload(contract_id, rating, comment)
    payload_hash = _payload_hash(payload)

    try:
        actor = require_active_actor(actor_user_id, ("CLIENTE",))
        contract = _lock_contract(contract_id)
        _require_contract_eligibility(contract, actor)

        command, replay = _begin_command(
            actor_user_id,
            idempotency_key,
            payload_hash,
            correlation_id,
            contract,
        )
        if replay is not None:
            db.session.rollback()
            return replay

        if Review.query.filter_by(contract_id=contract.id).first() is not None:
            raise ContractReviewConflictError(
                "La contratacion ya tiene una review"
            )

        review = _create_review(contract, command, rating, comment)
        _create_reputation_event(contract, review, command)
        _create_audit_log(contract, review, command)
        _create_notification(contract, review, command)
        _complete_command(command, review)
        db.session.commit()
        return review
    except IntegrityError:
        db.session.rollback()
        recovered = _recover_integrity_race(
            actor_user_id,
            contract_id,
            idempotency_key,
            payload_hash,
        )
        if recovered is not None:
            return recovered
        raise
    except Exception:
        db.session.rollback()
        raise


__all__ = (
    "ContractReviewConflictError",
    "ContractReviewIdempotencyConflictError",
    "ContractReviewIntegrityError",
    "OPERATION_CREATE_CONTRACT_REVIEW",
    "create_contract_review",
)
