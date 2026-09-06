import hashlib
import hmac
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from app import db
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.contract_event import ContractEvent
from app.models.contract_negotiation import ContractNegotiation
from app.models.contract_negotiation_version import ContractNegotiationVersion
from app.models.contract_request import ContractRequest
from app.models.negotiation_acceptance import NegotiationAcceptance
from app.models.negotiation_event import NegotiationEvent
from app.models.operation_command import OperationCommand
from app.models.professional import Professional
from app.models.user import User
from app.services.actor_policy_service import require_active_actor
from app.services.contract_service import (
    ContractConflictError,
    IdempotencyConflictError,
    require_idempotency_key,
)
from app.services.notification_service import (
    CATEGORIA_CONTRATACIONES,
    PRIORIDAD_ACCION_REQUERIDA,
    PRIORIDAD_INFO,
)


class NegotiationConflictError(ContractConflictError):
    """The command conflicts with the current negotiation version."""


OPERATION_INITIATE = "INITIATE_DIRECT_NEGOTIATION"
OPERATION_PROPOSE = "PROPOSE_NEGOTIATION_TERMS"
OPERATION_ACCEPT = "ACCEPT_NEGOTIATION_TERMS"
OPERATION_CANCEL = "CANCEL_NEGOTIATION"
OPERATION_REJECT = "REJECT_NEGOTIATION"
OPERATION_FINALIZE = "FINALIZE_NEGOTIATION_CONTRACT"

RESULT_NEGOTIATION = "ContractNegotiation"
RESULT_CONTRACT = "ContractRequest"


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _payload_hash(payload):
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _derived_key(prefix, *parts):
    digest = hashlib.sha256(
        ":".join(str(part) for part in parts).encode("utf-8")
    ).hexdigest()
    return f"{prefix}:{digest}"


def _required_text(value, label, maximum):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} obligatorio")
    normalized = value.strip()
    if len(normalized) > maximum:
        raise ValueError(f"{label} demasiado largo")
    return normalized


def _optional_text(value, label, maximum):
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValueError(f"{label} invalido")
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > maximum:
        raise ValueError(f"{label} demasiado largo")
    return normalized


def _normalize_terms(
    *,
    description,
    scope,
    external_price,
    estimated_start_at=None,
    estimated_end_at=None,
    observations=None,
):
    try:
        price = Decimal(str(external_price)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Precio externo invalido") from None
    if price < 0 or price > Decimal("99999999.99"):
        raise ValueError("Precio externo fuera de rango")
    if estimated_start_at and estimated_end_at:
        if estimated_start_at > estimated_end_at:
            raise ValueError(
                "La fecha estimada de inicio no puede superar la finalizacion"
            )
    return {
        "description": _required_text(description, "Descripcion", 5000),
        "scope": _required_text(scope, "Alcance", 5000),
        "external_price": price,
        "estimated_start_at": estimated_start_at,
        "estimated_end_at": estimated_end_at,
        "observations": _optional_text(
            observations,
            "Observaciones",
            3000,
        ),
    }


def _canonical_terms_datetime(value):
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.isoformat(timespec="microseconds")


def _canonical_terms_content(
    *,
    description,
    scope,
    external_price,
    estimated_start_at,
    estimated_end_at,
    observations,
):
    price = Decimal(str(external_price)).quantize(Decimal("0.01"))
    return {
        "description": description,
        "scope": scope,
        "external_price": format(price, "f"),
        "estimated_start_at": _canonical_terms_datetime(estimated_start_at),
        "estimated_end_at": _canonical_terms_datetime(estimated_end_at),
        "observations": observations,
    }


def _canonical_terms_hash_from_data(terms_data):
    return _payload_hash(_canonical_terms_content(**terms_data))


def _canonical_terms_hash(terms):
    return _payload_hash(
        _canonical_terms_content(
            description=terms.description,
            scope=terms.scope,
            external_price=terms.external_price,
            estimated_start_at=terms.estimated_start_at,
            estimated_end_at=terms.estimated_end_at,
            observations=terms.observations,
        )
    )


def _find_command(actor_user_id, operation, idempotency_key, lock=False):
    query = OperationCommand.query.filter_by(
        actor_user_id=actor_user_id,
        operation=operation,
        idempotency_key=idempotency_key,
    )
    if lock:
        query = query.with_for_update()
    return query.first()


def _load_command_result(command):
    if (
        command.result_entity_type == RESULT_NEGOTIATION
        and command.result_entity_id is not None
    ):
        return db.session.get(ContractNegotiation, command.result_entity_id)
    if (
        command.result_entity_type == RESULT_CONTRACT
        and command.result_entity_id is not None
    ):
        return db.session.get(ContractRequest, command.result_entity_id)
    return None


def _replay_or_conflict(command, expected_payload_hash):
    if command.payload_hash != expected_payload_hash:
        raise IdempotencyConflictError(
            "La idempotency key ya fue usada con un payload diferente"
        )
    if command.status == OperationCommand.STATUS_PROCESSING:
        raise NegotiationConflictError("Comando en proceso; reintento permitido")
    if command.status == OperationCommand.STATUS_FAILED:
        raise NegotiationConflictError(
            f"El comando previo fallo: {command.failure_code or 'UNKNOWN'}"
        )
    result = _load_command_result(command)
    if result is None:
        raise NegotiationConflictError(
            "El resultado idempotente ya no esta disponible"
        )
    return result


def _begin_command(actor_user_id, operation, idempotency_key, payload_hash):
    existing = _find_command(
        actor_user_id,
        operation,
        idempotency_key,
        lock=True,
    )
    if existing is not None:
        return existing, _replay_or_conflict(existing, payload_hash)
    command = OperationCommand(
        actor_user_id=actor_user_id,
        operation=operation,
        idempotency_key=idempotency_key,
        payload_hash=payload_hash,
        status=OperationCommand.STATUS_PROCESSING,
        correlation_id=str(uuid4()),
    )
    db.session.add(command)
    db.session.flush()
    return command, None


def _complete_command(command, result, result_type):
    command.status = OperationCommand.STATUS_SUCCEEDED
    command.result_entity_type = result_type
    command.result_entity_id = result.id
    command.completed_at = _utcnow()
    command.failure_code = None


def _recover_integrity_race(
    actor_user_id,
    operation,
    idempotency_key,
    payload_hash,
):
    db.session.rollback()
    existing = _find_command(actor_user_id, operation, idempotency_key)
    if existing is None:
        return None
    return _replay_or_conflict(existing, payload_hash)


def _lock_negotiation(negotiation_id):
    negotiation = (
        ContractNegotiation.query.filter_by(id=negotiation_id)
        .with_for_update()
        .first()
    )
    if negotiation is None:
        raise LookupError("Negociacion no encontrada")
    return negotiation


def _party_for_actor(negotiation, actor):
    if actor.rol == "CLIENTE" and negotiation.cliente_id == actor.id:
        return NegotiationAcceptance.PARTY_CLIENT
    if (
        actor.rol == "PROFESIONAL"
        and negotiation.professional_user_id == actor.id
    ):
        return NegotiationAcceptance.PARTY_PROFESSIONAL
    raise PermissionError("No perteneces a esta negociacion")


def _authorize_negotiation(negotiation, actor_user_id):
    actor = require_active_actor(actor_user_id, ("CLIENTE", "PROFESIONAL"))
    party = _party_for_actor(negotiation, actor)
    return actor, party


def _current_terms(negotiation, lock=False):
    query = ContractNegotiationVersion.query.filter_by(
        negotiation_id=negotiation.id,
        version_no=negotiation.current_terms_version,
    )
    if lock:
        query = query.with_for_update()
    terms = query.first()
    if terms is None:
        raise NegotiationConflictError("La version vigente no esta disponible")
    return _verify_terms_integrity(negotiation, terms)


def _verify_terms_integrity(negotiation, terms):
    if (
        terms.negotiation_id != negotiation.id
        or terms.version_no != negotiation.current_terms_version
    ):
        raise NegotiationConflictError(
            "El snapshot vigente no corresponde a la negociacion bloqueada"
        )
    expected_hash = _canonical_terms_hash(terms)
    if not hmac.compare_digest(terms.payload_hash or "", expected_hash):
        raise NegotiationConflictError(
            "El snapshot de terminos fue alterado y no puede utilizarse"
        )
    return terms


def _validate_acceptance_identity(negotiation, terms, acceptance):
    if (
        acceptance.negotiation_id != negotiation.id
        or acceptance.negotiation_version_id != terms.id
        or terms.negotiation_id != negotiation.id
        or terms.version_no != negotiation.current_terms_version
    ):
        raise NegotiationConflictError(
            "La aceptacion no corresponde a la version vigente"
        )
    if acceptance.party == NegotiationAcceptance.PARTY_CLIENT:
        expected_actor_id = negotiation.cliente_id
        expected_role = "CLIENTE"
    elif acceptance.party == NegotiationAcceptance.PARTY_PROFESSIONAL:
        expected_actor_id = negotiation.professional_user_id
        expected_role = "PROFESIONAL"
    else:
        raise NegotiationConflictError("Parte de aceptacion invalida")
    if acceptance.actor_user_id != expected_actor_id:
        raise NegotiationConflictError(
            "La identidad de la aceptacion no coincide con la parte"
        )
    actor = db.session.get(User, acceptance.actor_user_id)
    if (
        actor is None
        or actor.estado != "ACTIVO"
        or actor.rol != expected_role
    ):
        raise PermissionError(
            "El actor de la aceptacion ya no conserva identidad y rol validos"
        )


def _validated_acceptance_parties(negotiation, terms):
    _verify_terms_integrity(negotiation, terms)
    rows = NegotiationAcceptance.query.filter_by(
        negotiation_id=negotiation.id,
        negotiation_version_id=terms.id,
    ).all()
    parties = set()
    for acceptance in rows:
        _validate_acceptance_identity(negotiation, terms, acceptance)
        if acceptance.party in parties:
            raise NegotiationConflictError(
                "Existen aceptaciones duplicadas para la misma parte"
            )
        parties.add(acceptance.party)
    return parties


def _next_event_sequence(negotiation_id):
    current = (
        db.session.query(db.func.max(NegotiationEvent.sequence_no))
        .filter(NegotiationEvent.negotiation_id == negotiation_id)
        .scalar()
    )
    return int(current or 0) + 1


def _record_event(
    negotiation,
    command,
    actor_user_id,
    event_type,
    *,
    terms_version=None,
    metadata=None,
):
    event = NegotiationEvent(
        negotiation_id=negotiation.id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        sequence_no=_next_event_sequence(negotiation.id),
        terms_version=terms_version,
        correlation_id=command.correlation_id,
        idempotency_key=_derived_key(
            "negotiation-event",
            actor_user_id,
            command.operation,
            command.idempotency_key,
            event_type,
        ),
        metadata_json=metadata or {},
    )
    db.session.add(event)
    db.session.flush()
    return event


def _add_audit(negotiation, event, command, target_user_id):
    db.session.add(
        AuditLog(
            actor_user_id=event.actor_user_id,
            target_user_id=target_user_id,
            action=event.event_type,
            description=(
                f"Negociacion #{negotiation.id}: {event.event_type} "
                f"en version de terminos {event.terms_version or '-'}."
            ),
            entity_type="ContractNegotiation",
            entity_id=negotiation.id,
            negotiation_event_id=event.id,
            correlation_id=command.correlation_id,
            operation=command.operation,
            idempotency_key=command.idempotency_key,
            metadata_json={
                "negotiation_version": negotiation.version,
                "terms_version": event.terms_version,
                "state": negotiation.state,
            },
        )
    )


def _counterparty_user_id(negotiation, actor_user_id):
    if actor_user_id == negotiation.cliente_id:
        return negotiation.professional_user_id
    return negotiation.cliente_id


def _add_notification(
    negotiation,
    event,
    command,
    recipient_user_id,
    *,
    title,
    message,
    requires_action=True,
):
    db.session.add(
        ActivityNotification(
            user_id=recipient_user_id,
            actor_user_id=event.actor_user_id,
            negotiation_event_id=event.id,
            correlation_id=command.correlation_id,
            idempotency_key=_derived_key(
                "negotiation-notification",
                command.actor_user_id,
                command.operation,
                command.idempotency_key,
                recipient_user_id,
                event.event_type,
            ),
            template_key=f"NEGOTIATION_{event.event_type}",
            channel="INTERNAL",
            delivery_status="DELIVERED",
            attempt_count=0,
            tipo=f"NEGOTIATION_{event.event_type}",
            categoria=CATEGORIA_CONTRATACIONES,
            titulo=title,
            mensaje=message,
            url_destino=f"/negociacion/{negotiation.id}",
            entity_type="ContractNegotiation",
            entity_id=negotiation.id,
            prioridad=(
                PRIORIDAD_ACCION_REQUERIDA
                if requires_action
                else PRIORIDAD_INFO
            ),
            requiere_accion=requires_action,
        )
    )


def _require_expected_version(negotiation, expected_version):
    try:
        parsed = int(expected_version)
    except (TypeError, ValueError):
        raise NegotiationConflictError("Version de negociacion obligatoria") from None
    if negotiation.version != parsed:
        raise NegotiationConflictError(
            f"Version desactualizada: esperada {parsed}, actual {negotiation.version}"
        )


def _require_terms_version(negotiation, terms_version):
    try:
        parsed = int(terms_version)
    except (TypeError, ValueError):
        raise NegotiationConflictError("Version de terminos obligatoria") from None
    if negotiation.current_terms_version != parsed:
        raise NegotiationConflictError(
            "La accion no corresponde a la version vigente de terminos"
        )
    return parsed


def _return_authorized_replay(result, actor_user_id):
    if isinstance(result, ContractNegotiation):
        _authorize_negotiation(result, actor_user_id)
        return result
    if isinstance(result, ContractRequest):
        if result.cliente_id != actor_user_id:
            raise PermissionError("Resultado idempotente no autorizado")
        return result
    raise NegotiationConflictError("Resultado idempotente incompatible")


def initiate_direct_negotiation(
    *,
    cliente_id,
    professional_id,
    servicio,
    description,
    scope,
    external_price,
    estimated_start_at=None,
    estimated_end_at=None,
    observations=None,
    actor_user_id,
    idempotency_key,
):
    actor = require_active_actor(actor_user_id, ("CLIENTE",))
    authorized_actor_id = actor.id
    if actor.id != cliente_id:
        raise PermissionError("Solo el cliente puede iniciar su negociacion")
    idempotency_key = require_idempotency_key(idempotency_key)
    service_name = _required_text(servicio, "Servicio", 120)
    terms_data = _normalize_terms(
        description=description,
        scope=scope,
        external_price=external_price,
        estimated_start_at=estimated_start_at,
        estimated_end_at=estimated_end_at,
        observations=observations,
    )
    professional = db.session.get(Professional, professional_id)
    if professional is None or professional.user_id is None:
        raise ValueError("Profesional invalido")
    professional_user = db.session.get(User, professional.user_id)
    if (
        professional_user is None
        or professional_user.estado != "ACTIVO"
        or professional_user.rol != "PROFESIONAL"
    ):
        raise ValueError("Usuario profesional activo requerido")
    if professional_user.id == actor.id:
        raise ValueError("No podes negociar con tu propio perfil")

    payload = {
        "cliente_id": cliente_id,
        "professional_id": professional_id,
        "professional_user_id": professional_user.id,
        "servicio": service_name,
        **terms_data,
    }
    command_payload_hash = _payload_hash(payload)
    try:
        command, replay = _begin_command(
            actor.id,
            OPERATION_INITIATE,
            idempotency_key,
            command_payload_hash,
        )
        if replay is not None:
            db.session.rollback()
            return _return_authorized_replay(replay, authorized_actor_id)

        negotiation = ContractNegotiation(
            cliente_id=actor.id,
            professional_id=professional.id,
            professional_user_id=professional_user.id,
            servicio=service_name,
            state=ContractNegotiation.STATE_OPEN,
            contracting_mode="EXTERNAL",
            version=1,
            current_terms_version=1,
            updated_at=_utcnow(),
        )
        db.session.add(negotiation)
        db.session.flush()
        terms = ContractNegotiationVersion(
            negotiation_id=negotiation.id,
            version_no=1,
            actor_user_id=actor.id,
            payload_hash=_canonical_terms_hash_from_data(terms_data),
            **terms_data,
        )
        db.session.add(terms)
        event = _record_event(
            negotiation,
            command,
            actor.id,
            NegotiationEvent.CREATED,
            terms_version=1,
        )
        _add_audit(negotiation, event, command, professional_user.id)
        _add_notification(
            negotiation,
            event,
            command,
            professional_user.id,
            title="Nueva negociacion directa",
            message=f"Recibiste terminos para {service_name}.",
        )
        _complete_command(command, negotiation, RESULT_NEGOTIATION)
        db.session.commit()
        return negotiation
    except IntegrityError:
        recovered = _recover_integrity_race(
            authorized_actor_id,
            OPERATION_INITIATE,
            idempotency_key,
            command_payload_hash,
        )
        if recovered is not None:
            return _return_authorized_replay(recovered, authorized_actor_id)
        raise
    except Exception:
        db.session.rollback()
        raise


def get_negotiation_for_actor(negotiation_id, *, actor_user_id):
    actor = require_active_actor(actor_user_id, ("CLIENTE", "PROFESIONAL"))
    negotiation = db.session.get(ContractNegotiation, negotiation_id)
    if negotiation is None:
        raise LookupError("Negociacion no encontrada")
    _party_for_actor(negotiation, actor)
    terms = _current_terms(negotiation)
    accepted_parties = _validated_acceptance_parties(negotiation, terms)
    return {
        "negotiation": negotiation,
        "current_terms": terms,
        "accepted_parties": accepted_parties,
        "actor_party": _party_for_actor(negotiation, actor),
    }


def propose_negotiation_terms(
    negotiation_id,
    *,
    description,
    scope,
    external_price,
    estimated_start_at=None,
    estimated_end_at=None,
    observations=None,
    actor_user_id,
    expected_version,
    idempotency_key,
):
    actor = require_active_actor(actor_user_id, ("CLIENTE", "PROFESIONAL"))
    authorized_actor_id = actor.id
    idempotency_key = require_idempotency_key(idempotency_key)
    terms_data = _normalize_terms(
        description=description,
        scope=scope,
        external_price=external_price,
        estimated_start_at=estimated_start_at,
        estimated_end_at=estimated_end_at,
        observations=observations,
    )
    payload = {
        "negotiation_id": negotiation_id,
        "expected_version": expected_version,
        **terms_data,
    }
    command_payload_hash = _payload_hash(payload)
    try:
        negotiation = _lock_negotiation(negotiation_id)
        _party_for_actor(negotiation, actor)
        command, replay = _begin_command(
            actor.id,
            OPERATION_PROPOSE,
            idempotency_key,
            command_payload_hash,
        )
        if replay is not None:
            db.session.rollback()
            return _return_authorized_replay(replay, authorized_actor_id)
        _require_expected_version(negotiation, expected_version)
        if negotiation.state != ContractNegotiation.STATE_OPEN:
            raise ValueError("La negociacion no admite nuevas propuestas")

        next_version = negotiation.current_terms_version + 1
        terms = ContractNegotiationVersion(
            negotiation_id=negotiation.id,
            version_no=next_version,
            actor_user_id=actor.id,
            payload_hash=_canonical_terms_hash_from_data(terms_data),
            **terms_data,
        )
        db.session.add(terms)
        negotiation.current_terms_version = next_version
        negotiation.agreed_terms_version = None
        negotiation.version += 1
        negotiation.updated_at = _utcnow()
        event = _record_event(
            negotiation,
            command,
            actor.id,
            NegotiationEvent.TERMS_PROPOSED,
            terms_version=next_version,
        )
        recipient_id = _counterparty_user_id(negotiation, actor.id)
        _add_audit(negotiation, event, command, recipient_id)
        _add_notification(
            negotiation,
            event,
            command,
            recipient_id,
            title="Nuevos terminos de negociacion",
            message=f"Se propuso la version {next_version} de los terminos.",
        )
        _complete_command(command, negotiation, RESULT_NEGOTIATION)
        db.session.commit()
        return negotiation
    except IntegrityError:
        recovered = _recover_integrity_race(
            authorized_actor_id,
            OPERATION_PROPOSE,
            idempotency_key,
            command_payload_hash,
        )
        if recovered is not None:
            return _return_authorized_replay(recovered, authorized_actor_id)
        raise
    except Exception:
        db.session.rollback()
        raise


def accept_negotiation_terms(
    negotiation_id,
    *,
    actor_user_id,
    expected_version,
    terms_version,
    idempotency_key,
):
    actor = require_active_actor(actor_user_id, ("CLIENTE", "PROFESIONAL"))
    authorized_actor_id = actor.id
    idempotency_key = require_idempotency_key(idempotency_key)
    payload = {
        "negotiation_id": negotiation_id,
        "expected_version": expected_version,
        "terms_version": terms_version,
    }
    command_payload_hash = _payload_hash(payload)
    try:
        negotiation = _lock_negotiation(negotiation_id)
        party = _party_for_actor(negotiation, actor)
        terms = _current_terms(negotiation, lock=True)
        command, replay = _begin_command(
            actor.id,
            OPERATION_ACCEPT,
            idempotency_key,
            command_payload_hash,
        )
        if replay is not None:
            db.session.rollback()
            return _return_authorized_replay(replay, authorized_actor_id)
        _require_expected_version(negotiation, expected_version)
        parsed_terms_version = _require_terms_version(
            negotiation,
            terms_version,
        )
        if negotiation.state != ContractNegotiation.STATE_OPEN:
            raise ValueError("La negociacion no esta abierta")
        existing = NegotiationAcceptance.query.filter_by(
            negotiation_version_id=terms.id,
            party=party,
        ).first()
        if existing is not None:
            raise NegotiationConflictError(
                "La parte ya acepto esta version de terminos"
            )
        acceptance = NegotiationAcceptance(
            negotiation_id=negotiation.id,
            negotiation_version_id=terms.id,
            actor_user_id=actor.id,
            party=party,
        )
        db.session.add(acceptance)
        db.session.flush()
        _validate_acceptance_identity(
            negotiation,
            terms,
            acceptance,
        )
        negotiation.version += 1
        negotiation.updated_at = _utcnow()
        event = _record_event(
            negotiation,
            command,
            actor.id,
            NegotiationEvent.TERMS_ACCEPTED,
            terms_version=parsed_terms_version,
            metadata={"party": party},
        )
        recipient_id = _counterparty_user_id(negotiation, actor.id)
        _add_audit(negotiation, event, command, recipient_id)
        _add_notification(
            negotiation,
            event,
            command,
            recipient_id,
            title="Terminos aceptados",
            message=f"La contraparte acepto la version {parsed_terms_version}.",
        )

        accepted_parties = _validated_acceptance_parties(
            negotiation,
            terms,
        )
        if accepted_parties == set(NegotiationAcceptance.PARTIES):
            negotiation.state = ContractNegotiation.STATE_AGREED
            negotiation.agreed_terms_version = parsed_terms_version
            agreed_event = _record_event(
                negotiation,
                command,
                actor.id,
                NegotiationEvent.AGREED,
                terms_version=parsed_terms_version,
            )
            _add_audit(negotiation, agreed_event, command, recipient_id)

        _complete_command(command, negotiation, RESULT_NEGOTIATION)
        db.session.commit()
        return negotiation
    except IntegrityError:
        recovered = _recover_integrity_race(
            authorized_actor_id,
            OPERATION_ACCEPT,
            idempotency_key,
            command_payload_hash,
        )
        if recovered is not None:
            return _return_authorized_replay(recovered, authorized_actor_id)
        raise
    except Exception:
        db.session.rollback()
        raise


def _terminate_negotiation(
    negotiation_id,
    *,
    actor_user_id,
    expected_version,
    idempotency_key,
    operation,
    target_state,
    event_type,
    required_party,
):
    actor = require_active_actor(actor_user_id, ("CLIENTE", "PROFESIONAL"))
    authorized_actor_id = actor.id
    idempotency_key = require_idempotency_key(idempotency_key)
    payload = {
        "negotiation_id": negotiation_id,
        "expected_version": expected_version,
        "target_state": target_state,
    }
    command_payload_hash = _payload_hash(payload)
    try:
        negotiation = _lock_negotiation(negotiation_id)
        party = _party_for_actor(negotiation, actor)
        if party != required_party:
            raise PermissionError("La parte no puede ejecutar esta accion")
        command, replay = _begin_command(
            actor.id,
            operation,
            idempotency_key,
            command_payload_hash,
        )
        if replay is not None:
            db.session.rollback()
            return _return_authorized_replay(replay, authorized_actor_id)
        _require_expected_version(negotiation, expected_version)
        if negotiation.state not in (
            ContractNegotiation.STATE_OPEN,
            ContractNegotiation.STATE_AGREED,
        ):
            raise ValueError("La negociacion ya es terminal")
        negotiation.state = target_state
        negotiation.version += 1
        negotiation.updated_at = _utcnow()
        event = _record_event(
            negotiation,
            command,
            actor.id,
            event_type,
            terms_version=negotiation.current_terms_version,
        )
        recipient_id = _counterparty_user_id(negotiation, actor.id)
        _add_audit(negotiation, event, command, recipient_id)
        _add_notification(
            negotiation,
            event,
            command,
            recipient_id,
            title="Negociacion finalizada",
            message=(
                "El cliente cancelo la negociacion."
                if target_state == ContractNegotiation.STATE_CANCELLED
                else "El profesional rechazo la negociacion."
            ),
            requires_action=False,
        )
        _complete_command(command, negotiation, RESULT_NEGOTIATION)
        db.session.commit()
        return negotiation
    except IntegrityError:
        recovered = _recover_integrity_race(
            authorized_actor_id,
            operation,
            idempotency_key,
            command_payload_hash,
        )
        if recovered is not None:
            return _return_authorized_replay(recovered, authorized_actor_id)
        raise
    except Exception:
        db.session.rollback()
        raise


def cancel_negotiation(
    negotiation_id,
    *,
    actor_user_id,
    expected_version,
    idempotency_key,
):
    return _terminate_negotiation(
        negotiation_id,
        actor_user_id=actor_user_id,
        expected_version=expected_version,
        idempotency_key=idempotency_key,
        operation=OPERATION_CANCEL,
        target_state=ContractNegotiation.STATE_CANCELLED,
        event_type=NegotiationEvent.CANCELLED,
        required_party=NegotiationAcceptance.PARTY_CLIENT,
    )


def reject_negotiation(
    negotiation_id,
    *,
    actor_user_id,
    expected_version,
    idempotency_key,
):
    return _terminate_negotiation(
        negotiation_id,
        actor_user_id=actor_user_id,
        expected_version=expected_version,
        idempotency_key=idempotency_key,
        operation=OPERATION_REJECT,
        target_state=ContractNegotiation.STATE_REJECTED,
        event_type=NegotiationEvent.REJECTED,
        required_party=NegotiationAcceptance.PARTY_PROFESSIONAL,
    )


def _contract_description(terms):
    parts = [terms.description, f"Alcance:\n{terms.scope}"]
    if terms.observations:
        parts.append(f"Observaciones:\n{terms.observations}")
    return "\n\n".join(parts)


def _create_contract_effects(negotiation, terms, command, actor_user_id):
    contract = ContractRequest(
        cliente_id=negotiation.cliente_id,
        professional_id=negotiation.professional_id,
        professional_user_id=negotiation.professional_user_id,
        servicio=negotiation.servicio,
        descripcion=_contract_description(terms),
        precio_acordado=terms.external_price,
        fecha_inicio=terms.estimated_start_at,
        fecha_fin=terms.estimated_end_at,
        source_type=ContractRequest.SOURCE_DIRECT,
        source_id=None,
        created_from_event=ContractEvent.CONTRACT_CREATED,
        estado="CREADA",
        contracting_mode=ContractRequest.CONTRACTING_MODE_EXTERNAL,
        version=1,
    )
    db.session.add(contract)
    db.session.flush()
    contract_event = ContractEvent(
        contract_id=contract.id,
        event_type=ContractEvent.CONTRACT_CREATED,
        actor_user_id=actor_user_id,
        sequence_no=1,
        correlation_id=command.correlation_id,
        idempotency_key=_derived_key(
            "contract-event-from-negotiation",
            negotiation.id,
            command.idempotency_key,
        ),
        previous_status=None,
        new_status=contract.estado,
        metadata_json={
            "source_type": ContractRequest.SOURCE_DIRECT,
            "contract_version": contract.version,
            "negotiation_id": negotiation.id,
            "negotiation_terms_version": terms.version_no,
        },
    )
    db.session.add(contract_event)
    db.session.flush()
    db.session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            target_user_id=negotiation.professional_user_id,
            action=ContractEvent.CONTRACT_CREATED,
            description=(
                f"Contrato #{contract.id} creado desde negociacion "
                f"#{negotiation.id}."
            ),
            entity_type="ContractRequest",
            entity_id=contract.id,
            contract_id=contract.id,
            event_id=contract_event.id,
            correlation_id=command.correlation_id,
            operation=command.operation,
            idempotency_key=command.idempotency_key,
            metadata_json={
                "contract_version": contract.version,
                "negotiation_id": negotiation.id,
                "negotiation_terms_version": terms.version_no,
            },
        )
    )
    db.session.add(
        ActivityNotification(
            user_id=negotiation.professional_user_id,
            actor_user_id=actor_user_id,
            contract_event_id=contract_event.id,
            correlation_id=command.correlation_id,
            idempotency_key=_derived_key(
                "contract-notification-from-negotiation",
                negotiation.id,
                command.idempotency_key,
            ),
            template_key="CONTRACT_CREATED",
            channel="INTERNAL",
            delivery_status="DELIVERED",
            attempt_count=0,
            tipo="CONTRACT_CREATED",
            categoria=CATEGORIA_CONTRATACIONES,
            titulo="Nueva contratacion",
            mensaje="El cliente materializo los terminos acordados.",
            url_destino=f"/contratacion/{contract.id}",
            entity_type="ContractRequest",
            entity_id=contract.id,
            prioridad=PRIORIDAD_ACCION_REQUERIDA,
            requiere_accion=True,
        )
    )
    return contract


def finalize_negotiation_contract(
    negotiation_id,
    *,
    actor_user_id,
    expected_version,
    terms_version,
    idempotency_key,
):
    actor = require_active_actor(actor_user_id, ("CLIENTE",))
    authorized_actor_id = actor.id
    idempotency_key = require_idempotency_key(idempotency_key)
    payload = {
        "negotiation_id": negotiation_id,
        "expected_version": expected_version,
        "terms_version": terms_version,
    }
    command_payload_hash = _payload_hash(payload)
    try:
        negotiation = _lock_negotiation(negotiation_id)
        party = _party_for_actor(negotiation, actor)
        if party != NegotiationAcceptance.PARTY_CLIENT:
            raise PermissionError("Solo el cliente puede crear el contrato")
        terms = _current_terms(negotiation, lock=True)
        accepted_parties = _validated_acceptance_parties(
            negotiation,
            terms,
        )
        command, replay = _begin_command(
            actor.id,
            OPERATION_FINALIZE,
            idempotency_key,
            command_payload_hash,
        )
        if replay is not None:
            db.session.rollback()
            return _return_authorized_replay(replay, authorized_actor_id)
        _require_expected_version(negotiation, expected_version)
        parsed_terms_version = _require_terms_version(
            negotiation,
            terms_version,
        )
        if (
            negotiation.state != ContractNegotiation.STATE_AGREED
            or negotiation.agreed_terms_version != parsed_terms_version
        ):
            raise ValueError("La negociacion no tiene terminos vigentes acordados")
        if accepted_parties != set(NegotiationAcceptance.PARTIES):
            raise NegotiationConflictError(
                "Faltan aceptaciones expresas para la version acordada"
            )
        professional_user = db.session.get(User, negotiation.professional_user_id)
        if (
            professional_user is None
            or professional_user.estado != "ACTIVO"
            or professional_user.rol != "PROFESIONAL"
        ):
            raise PermissionError("El profesional ya no esta habilitado")
        if negotiation.contract_id is not None:
            raise NegotiationConflictError("La negociacion ya tiene contrato")

        contract = _create_contract_effects(
            negotiation,
            terms,
            command,
            actor.id,
        )
        negotiation.state = ContractNegotiation.STATE_CONTRACTED
        negotiation.contract_id = contract.id
        negotiation.version += 1
        negotiation.updated_at = _utcnow()
        negotiation_event = _record_event(
            negotiation,
            command,
            actor.id,
            NegotiationEvent.CONTRACT_CREATED,
            terms_version=parsed_terms_version,
            metadata={"contract_id": contract.id},
        )
        _add_audit(
            negotiation,
            negotiation_event,
            command,
            negotiation.professional_user_id,
        )
        _complete_command(command, contract, RESULT_CONTRACT)
        db.session.commit()
        return contract
    except IntegrityError:
        recovered = _recover_integrity_race(
            authorized_actor_id,
            OPERATION_FINALIZE,
            idempotency_key,
            command_payload_hash,
        )
        if recovered is not None:
            return _return_authorized_replay(recovered, authorized_actor_id)
        raise
    except Exception:
        db.session.rollback()
        raise


__all__ = (
    "NegotiationConflictError",
    "initiate_direct_negotiation",
    "propose_negotiation_terms",
    "accept_negotiation_terms",
    "cancel_negotiation",
    "reject_negotiation",
    "finalize_negotiation_contract",
    "get_negotiation_for_actor",
)
