import hashlib
import json
import re
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from app import db
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.contract_event import ContractEvent
from app.models.contract_request import ContractRequest
from app.models.operation_command import OperationCommand
from app.models.professional import Professional
from app.models.user import User
from app.services.actor_policy_service import require_active_actor
from app.services.notification_service import (
    CATEGORIA_CONTRATACIONES,
    PRIORIDAD_ACCION_REQUERIDA,
    PRIORIDAD_INFO,
)


class ContractConflictError(ValueError):
    """The command conflicts with the current aggregate or command version."""


class IdempotencyConflictError(ContractConflictError):
    """An idempotency key was reused with a different intent."""


IDEMPOTENCY_KEY_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{15,159}")


def require_idempotency_key(idempotency_key):
    if not isinstance(idempotency_key, str) or not idempotency_key:
        raise ValueError("Idempotency key obligatoria")
    if idempotency_key != idempotency_key.strip():
        raise ValueError("Idempotency key invalida")
    if IDEMPOTENCY_KEY_PATTERN.fullmatch(idempotency_key) is None:
        raise ValueError("Idempotency key invalida")
    return idempotency_key


TRANSITIONS = {
    "CREADA": frozenset(("ACEPTADA", "RECHAZADA", "CANCELADA")),
    "ACEPTADA": frozenset(("EN_PROGRESO", "CANCELADA")),
    "EN_PROGRESO": frozenset(("COMPLETADA", "CANCELADA")),
    "COMPLETADA": frozenset(("CONFIRMADA", "CORRECCION_SOLICITADA", "CANCELADA")),
    "CORRECCION_SOLICITADA": frozenset(("EN_PROGRESO", "COMPLETADA", "CANCELADA")),
    "CONFIRMADA": frozenset(),
    "RECHAZADA": frozenset(),
    "CANCELADA": frozenset(),
}

OPERATION_ACCEPT = "ACCEPT_CONTRACT"
OPERATION_REJECT = "REJECT_CONTRACT"
OPERATION_START = "START_CONTRACT"
OPERATION_COMPLETE = "DECLARE_WORK_COMPLETED"
OPERATION_CONFIRM = "CONFIRM_COMPLETION"
OPERATION_LEGACY_CANCEL = "CANCEL_CONTRACT_LEGACY"
OPERATION_CREATE_DIRECT = "CREATE_DIRECT_CONTRACT"

OPERATION_RULES = {
    OPERATION_ACCEPT: {
        "target": "ACEPTADA",
        "actor": "PROFESSIONAL",
        "event": ContractEvent.CONTRACT_ACCEPTED,
        "timestamp": "accepted_at",
    },
    OPERATION_REJECT: {
        "target": "RECHAZADA",
        "actor": "PROFESSIONAL",
        "event": ContractEvent.CONTRACT_REJECTED,
        "timestamp": None,
    },
    OPERATION_START: {
        "target": "EN_PROGRESO",
        "actor": "PROFESSIONAL",
        "event": ContractEvent.CONTRACT_STARTED,
        "timestamp": "started_at",
    },
    OPERATION_COMPLETE: {
        "target": "COMPLETADA",
        "actor": "PROFESSIONAL",
        "event": ContractEvent.CONTRACT_COMPLETED,
        "timestamp": "completed_at",
    },
    OPERATION_CONFIRM: {
        "target": "CONFIRMADA",
        "actor": "CLIENT",
        "event": ContractEvent.CONTRACT_CONFIRMED,
        "timestamp": "confirmed_at",
    },
    # Compatibility only. The consensual cancellation workflow belongs to Phase 2D.
    OPERATION_LEGACY_CANCEL: {
        "target": "CANCELADA",
        "actor": "CLIENT",
        "event": ContractEvent.CONTRACT_CANCELLED,
        "timestamp": "cancelled_at",
    },
}

NOTIFICATION_COPY = {
    ContractEvent.CONTRACT_CREATED: (
        "CONTRACT_CREATED",
        "Nueva contratacion",
        "El cliente creo una contratacion pendiente de tu aceptacion.",
        True,
    ),
    ContractEvent.CONTRACT_ACCEPTED: (
        "CONTRACT_ACCEPTED",
        "Contratacion aceptada",
        "El profesional acepto la contratacion.",
        False,
    ),
    ContractEvent.CONTRACT_REJECTED: (
        "CONTRACT_REJECTED",
        "Contratacion rechazada",
        "El profesional rechazo la contratacion.",
        False,
    ),
    ContractEvent.CONTRACT_STARTED: (
        "CONTRACT_STARTED",
        "Trabajo iniciado",
        "El profesional declaro iniciado el trabajo.",
        False,
    ),
    ContractEvent.CONTRACT_COMPLETED: (
        "CONTRACT_COMPLETED",
        "Trabajo declarado completado",
        "El profesional declaro que termino el trabajo. Revisa y confirma la finalizacion.",
        True,
    ),
    ContractEvent.CONTRACT_CONFIRMED: (
        "CONTRACT_CONFIRMED",
        "Finalizacion confirmada",
        "El cliente confirmo expresamente la finalizacion del trabajo.",
        False,
    ),
    ContractEvent.CONTRACT_CANCELLED: (
        "CONTRACT_CANCELLED",
        "Contratacion cancelada",
        "La contratacion fue cancelada sin determinar responsabilidad entre las partes.",
        False,
    ),
}


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalized_payload_hash(payload):
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _derived_key(prefix, *parts):
    digest = hashlib.sha256(":".join(str(part) for part in parts).encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def _require_actor(actor_user_id):
    return require_active_actor(
        actor_user_id,
        ("CLIENTE", "PROFESIONAL", "SUPER_ADMIN"),
    )


def _require_role_and_ownership(contract, actor, actor_kind):
    if actor_kind == "PROFESSIONAL":
        if actor.rol != "PROFESIONAL" or contract.professional_user_id != actor.id:
            raise PermissionError("Solo el profesional asignado puede ejecutar esta operacion")
        return
    if actor_kind == "CLIENT":
        if actor.rol != "CLIENTE" or contract.cliente_id != actor.id:
            raise PermissionError("Solo el cliente propietario puede ejecutar esta operacion")
        return
    raise RuntimeError("Regla de actor contractual invalida")


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


def _next_sequence(contract_id):
    current = (
        db.session.query(db.func.max(ContractEvent.sequence_no))
        .filter(ContractEvent.contract_id == contract_id)
        .scalar()
    )
    return int(current or 0) + 1


def _find_command(actor_user_id, operation, idempotency_key, lock=False):
    query = OperationCommand.query.filter_by(
        actor_user_id=actor_user_id,
        operation=operation,
        idempotency_key=idempotency_key,
    )
    if lock:
        query = query.with_for_update()
    return query.first()


def _replay_or_conflict(command, payload_hash):
    if command.payload_hash != payload_hash:
        raise IdempotencyConflictError(
            "La idempotency key ya fue usada con un payload diferente"
        )
    if command.status == OperationCommand.STATUS_PROCESSING:
        raise ContractConflictError("Comando en proceso; reintento permitido")
    if command.status == OperationCommand.STATUS_FAILED:
        raise ContractConflictError(
            f"El comando previo fallo: {command.failure_code or 'UNKNOWN'}"
        )
    if (
        command.result_entity_type != "ContractRequest"
        or command.result_entity_id is None
    ):
        raise ContractConflictError("El comando previo no tiene un resultado recuperable")
    result = db.session.get(ContractRequest, command.result_entity_id)
    if result is None:
        raise ContractConflictError("El resultado idempotente ya no esta disponible")
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


def _complete_command(command, contract):
    command.status = OperationCommand.STATUS_SUCCEEDED
    command.result_entity_type = "ContractRequest"
    command.result_entity_id = contract.id
    command.completed_at = _utcnow()
    command.failure_code = None


def _add_audit(contract, event, command, actor_user_id, target_user_id):
    db.session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            action=event.event_type,
            description=(
                f"Contratacion #{contract.id}: "
                f"{event.previous_status or '-'} -> {event.new_status or contract.estado}."
            ),
            entity_type="ContractRequest",
            entity_id=contract.id,
            contract_id=contract.id,
            event_id=event.id,
            correlation_id=command.correlation_id,
            operation=command.operation,
            idempotency_key=command.idempotency_key,
            metadata_json={
                "previous_status": event.previous_status,
                "new_status": event.new_status,
                "contract_version": contract.version,
            },
        )
    )


def _add_contract_notification(contract, event, command, recipient_user_id):
    tipo, titulo, mensaje, requires_action = NOTIFICATION_COPY[event.event_type]
    db.session.add(
        ActivityNotification(
            user_id=recipient_user_id,
            actor_user_id=event.actor_user_id,
            contract_event_id=event.id,
            correlation_id=command.correlation_id,
            idempotency_key=_derived_key(
                "notification",
                command.actor_user_id,
                command.operation,
                command.idempotency_key,
                recipient_user_id,
            ),
            template_key=tipo,
            channel="INTERNAL",
            delivery_status="DELIVERED",
            attempt_count=0,
            tipo=tipo,
            categoria=CATEGORIA_CONTRATACIONES,
            titulo=titulo,
            mensaje=mensaje,
            url_destino=f"/contratacion/{contract.id}",
            entity_type="ContractRequest",
            entity_id=contract.id,
            prioridad=PRIORIDAD_ACCION_REQUERIDA if requires_action else PRIORIDAD_INFO,
            requiere_accion=requires_action,
        )
    )


def _create_transition_event(contract, rule, command, actor_user_id, previous_status):
    event = ContractEvent(
        contract_id=contract.id,
        event_type=rule["event"],
        actor_user_id=actor_user_id,
        sequence_no=_next_sequence(contract.id),
        correlation_id=command.correlation_id,
        idempotency_key=_derived_key(
            "event",
            actor_user_id,
            command.operation,
            command.idempotency_key,
        ),
        previous_status=previous_status,
        new_status=rule["target"],
        metadata_json={"contract_version": contract.version},
    )
    db.session.add(event)
    db.session.flush()
    return event


def _recover_integrity_race(actor_user_id, operation, idempotency_key, payload_hash):
    db.session.rollback()
    existing = _find_command(actor_user_id, operation, idempotency_key)
    if existing is None:
        return None
    return _replay_or_conflict(existing, payload_hash)


def _execute_transition(
    contract_id,
    actor_user_id,
    operation,
    *,
    expected_version=None,
    idempotency_key=None,
):
    actor = _require_actor(actor_user_id)
    rule = OPERATION_RULES[operation]
    idempotency_key = idempotency_key or (
        f"compat:{contract_id}:{actor_user_id}:{operation}"
    )
    if len(idempotency_key) > 160:
        raise ValueError("Idempotency key demasiado larga")

    payload = {
        "contract_id": contract_id,
        "expected_version": expected_version,
        "operation": operation,
    }
    payload_hash = _normalized_payload_hash(payload)

    try:
        contract = _lock_contract(contract_id)
        _require_role_and_ownership(contract, actor, rule["actor"])

        command, replay = _begin_command(
            actor_user_id,
            operation,
            idempotency_key,
            payload_hash,
        )
        if replay is not None:
            db.session.rollback()
            return replay

        if expected_version is not None and contract.version != int(expected_version):
            raise ContractConflictError(
                f"Version desactualizada: esperada {expected_version}, actual {contract.version}"
            )

        target_status = rule["target"]
        if target_status not in TRANSITIONS.get(contract.estado, frozenset()):
            raise ValueError(f"Transicion invalida: {contract.estado} -> {target_status}")

        previous_status = contract.estado
        contract.estado = target_status
        contract.version += 1
        if rule["timestamp"]:
            setattr(contract, rule["timestamp"], _utcnow())

        event = _create_transition_event(
            contract,
            rule,
            command,
            actor_user_id,
            previous_status,
        )
        recipient_user_id = (
            contract.cliente_id
            if actor_user_id == contract.professional_user_id
            else contract.professional_user_id
        )
        if recipient_user_id is None:
            raise ValueError("La contraparte contractual no esta asociada")

        _add_audit(
            contract,
            event,
            command,
            actor_user_id,
            recipient_user_id,
        )
        _add_contract_notification(
            contract,
            event,
            command,
            recipient_user_id,
        )
        _complete_command(command, contract)
        db.session.commit()
        return contract
    except IntegrityError:
        recovered = _recover_integrity_race(
            actor_user_id,
            operation,
            idempotency_key,
            payload_hash,
        )
        if recovered is not None:
            return recovered
        raise
    except Exception:
        db.session.rollback()
        raise


def create_contract(
    cliente_id,
    professional_id,
    servicio,
    professional_user_id=None,
    descripcion=None,
    precio_acordado=None,
    fecha_inicio=None,
    fecha_fin=None,
    *,
    actor_user_id,
    idempotency_key,
):
    actor = _require_actor(actor_user_id)
    if actor.id != cliente_id or actor.rol != "CLIENTE":
        raise PermissionError("Solo el cliente propietario puede crear la contratacion")
    idempotency_key = require_idempotency_key(idempotency_key)

    professional = db.session.get(Professional, professional_id)
    if (
        professional is None
        or professional.user_id is None
        or professional.user_id != professional_user_id
    ):
        raise ValueError("Profesional asignado invalido")
    professional_user = db.session.get(User, professional_user_id)
    if professional_user is None or professional_user.rol != "PROFESIONAL":
        raise ValueError("Usuario profesional invalido")
    if professional_user_id == cliente_id:
        raise ValueError("No podes contratar tu propio perfil")

    payload_hash = _normalized_payload_hash(
        {
            "cliente_id": cliente_id,
            "professional_id": professional_id,
            "professional_user_id": professional_user_id,
            "servicio": servicio,
            "descripcion": descripcion,
            "precio_acordado": precio_acordado,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        }
    )

    try:
        command, replay = _begin_command(
            actor_user_id,
            OPERATION_CREATE_DIRECT,
            idempotency_key,
            payload_hash,
        )
        if replay is not None:
            db.session.rollback()
            if replay.cliente_id != actor_user_id:
                raise PermissionError("Resultado idempotente no autorizado")
            return replay

        contract = ContractRequest(
            cliente_id=cliente_id,
            professional_id=professional_id,
            professional_user_id=professional_user_id,
            servicio=servicio,
            descripcion=descripcion,
            precio_acordado=precio_acordado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            source_type=ContractRequest.SOURCE_DIRECT,
            source_id=None,
            created_from_event=ContractEvent.CONTRACT_CREATED,
            estado="CREADA",
            contracting_mode=ContractRequest.CONTRACTING_MODE_EXTERNAL,
            version=1,
        )
        db.session.add(contract)
        db.session.flush()

        event = ContractEvent(
            contract_id=contract.id,
            event_type=ContractEvent.CONTRACT_CREATED,
            actor_user_id=cliente_id,
            sequence_no=1,
            correlation_id=command.correlation_id,
            idempotency_key=_derived_key(
                "event",
                actor_user_id,
                OPERATION_CREATE_DIRECT,
                idempotency_key,
            ),
            previous_status=None,
            new_status=contract.estado,
            metadata_json={
                "source_type": ContractRequest.SOURCE_DIRECT,
                "contract_version": contract.version,
            },
        )
        db.session.add(event)
        db.session.flush()
        _add_audit(
            contract,
            event,
            command,
            cliente_id,
            professional_user_id,
        )

        _add_contract_notification(
            contract,
            event,
            command,
            professional_user_id,
        )

        _complete_command(command, contract)
        db.session.commit()
        return contract
    except IntegrityError:
        recovered = _recover_integrity_race(
            actor_user_id,
            OPERATION_CREATE_DIRECT,
            idempotency_key,
            payload_hash,
        )
        if recovered is not None:
            return recovered
        raise
    except Exception:
        db.session.rollback()
        raise


def get_contract_by_id(contract_id):
    return db.session.get(ContractRequest, contract_id)


def get_contract_or_error(contract_id):
    contract = get_contract_by_id(contract_id)
    if contract is None:
        raise LookupError("Contratacion no encontrada")
    return contract


def get_contract_detail_context(contract, user_id):
    is_client = contract.cliente_id == user_id
    is_professional = contract.professional_user_id == user_id
    if not is_client and not is_professional:
        raise PermissionError("No tenes permiso para ver esta contratacion")
    return {
        "contract": contract,
        "client_user": db.session.get(User, contract.cliente_id),
        "professional_user": db.session.get(User, contract.professional_user_id),
        "is_client": is_client,
        "is_professional": is_professional,
    }


def require_assigned_professional(contract, user_id):
    actor = _require_actor(user_id)
    _require_role_and_ownership(contract, actor, "PROFESSIONAL")


def require_client_owner(contract, user_id):
    actor = _require_actor(user_id)
    _require_role_and_ownership(contract, actor, "CLIENT")


def get_client_contracts(cliente_id):
    return (
        ContractRequest.query
        .filter_by(cliente_id=cliente_id)
        .order_by(ContractRequest.fecha_creacion.desc())
        .all()
    )


def get_professional_contracts(professional_id):
    return (
        ContractRequest.query
        .filter_by(professional_id=professional_id)
        .order_by(ContractRequest.fecha_creacion.desc())
        .all()
    )


def accept_contract(
    contract_id,
    professional_user_id,
    *,
    expected_version=None,
    idempotency_key=None,
):
    return _execute_transition(
        contract_id,
        professional_user_id,
        OPERATION_ACCEPT,
        expected_version=expected_version,
        idempotency_key=idempotency_key,
    )


def reject_contract(
    contract_id,
    professional_user_id,
    *,
    expected_version=None,
    idempotency_key=None,
):
    return _execute_transition(
        contract_id,
        professional_user_id,
        OPERATION_REJECT,
        expected_version=expected_version,
        idempotency_key=idempotency_key,
    )


def start_contract(
    contract_id,
    actor_user_id,
    *,
    expected_version=None,
    idempotency_key=None,
):
    return _execute_transition(
        contract_id,
        actor_user_id,
        OPERATION_START,
        expected_version=expected_version,
        idempotency_key=idempotency_key,
    )


def declare_work_completed(
    contract_id,
    actor_user_id,
    *,
    expected_version=None,
    idempotency_key=None,
):
    return _execute_transition(
        contract_id,
        actor_user_id,
        OPERATION_COMPLETE,
        expected_version=expected_version,
        idempotency_key=idempotency_key,
    )


def confirm_completion(
    contract_id,
    actor_user_id,
    *,
    expected_version=None,
    idempotency_key=None,
):
    return _execute_transition(
        contract_id,
        actor_user_id,
        OPERATION_CONFIRM,
        expected_version=expected_version,
        idempotency_key=idempotency_key,
    )


def cancel_contract(
    contract_id,
    actor_user_id,
    *,
    expected_version=None,
    idempotency_key=None,
):
    """Phase 1 compatibility; this is not the future consensual cancellation flow."""
    return _execute_transition(
        contract_id,
        actor_user_id,
        OPERATION_LEGACY_CANCEL,
        expected_version=expected_version,
        idempotency_key=idempotency_key,
    )


# Explicit compatibility aliases. They do not expose arbitrary destination states.
complete_contract = declare_work_completed
confirm_contract = confirm_completion
