from datetime import datetime

from app import db
from app.models.audit_log import AuditLog
from app.models.contract_event import ContractEvent
from app.models.user import User
from app.models.contract_request import ContractRequest


TRANSITIONS = {
    "CREADA": {"ACEPTADA", "RECHAZADA", "CANCELADA"},
    "ACEPTADA": {"EN_PROGRESO", "CANCELADA"},
    "EN_PROGRESO": {"COMPLETADA", "CANCELADA"},
    "COMPLETADA": {"CONFIRMADA"},
    "CONFIRMADA": {"CERRADA"},
}


def create_contract(
    cliente_id,
    professional_id,
    servicio,
    professional_user_id=None,
    descripcion=None,
    precio_acordado=None,
    fecha_inicio=None,
    fecha_fin=None
):
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
    )

    db.session.add(contract)
    db.session.flush()
    event = ContractEvent(
        contract_id=contract.id,
        event_type=ContractEvent.CONTRACT_CREATED,
        actor_user_id=cliente_id,
        previous_status=None,
        new_status=contract.estado,
        metadata_json={"source_type": ContractRequest.SOURCE_DIRECT},
    )
    db.session.add(event)
    db.session.flush()
    db.session.add(
        AuditLog(
            actor_user_id=cliente_id,
            target_user_id=professional_user_id,
            action=ContractEvent.CONTRACT_CREATED,
            description=f"Contrato #{contract.id} creado directamente.",
            entity_type="ContractRequest",
            entity_id=contract.id,
            contract_id=contract.id,
            event_id=event.id,
            idempotency_key=f"contract:DIRECT:{contract.id}",
        )
    )
    db.session.commit()

    return contract


def get_contract_by_id(contract_id):
    return ContractRequest.query.get(contract_id)


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
        "client_user": User.query.filter_by(id=contract.cliente_id).first(),
        "professional_user": User.query.filter_by(id=contract.professional_user_id).first(),
        "is_client": is_client,
        "is_professional": is_professional,
    }


def require_assigned_professional(contract, user_id):
    if contract.professional_user_id != user_id:
        raise PermissionError("Profesional no asignado a la contratacion")


def require_client_owner(contract, user_id):
    if contract.cliente_id != user_id:
        raise PermissionError("Solo el cliente dueno puede operar esta contratacion")


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


def assign_professional(contract_id, professional_user_id):
    contract = get_contract_by_id(contract_id)

    if contract is None:
        return None

    if contract.estado != "CREADA":
        raise ValueError("Solo se puede asignar profesional a una contratacion creada")

    contract.professional_user_id = professional_user_id
    db.session.commit()

    return contract


def _validate_professional_assignment(contract, professional_user_id):
    if contract.professional_user_id != professional_user_id:
        raise PermissionError("Profesional no asignado a la contratacion")


def _event_type_for_status(new_status):
    return {
        "ACEPTADA": ContractEvent.CONTRACT_ACCEPTED,
        "RECHAZADA": ContractEvent.CONTRACT_REJECTED,
        "EN_PROGRESO": ContractEvent.CONTRACT_STARTED,
        "COMPLETADA": ContractEvent.CONTRACT_COMPLETED,
        "CONFIRMADA": ContractEvent.CONTRACT_CONFIRMED,
        "CANCELADA": ContractEvent.CONTRACT_CANCELLED,
    }.get(new_status)


def _require_actor(actor_user_id):
    if actor_user_id is None:
        raise PermissionError("Actor requerido para operar la contratacion")


def _transition_contract(contract, new_status, timestamp_field=None, actor_user_id=None):
    _require_actor(actor_user_id)
    if new_status not in TRANSITIONS.get(contract.estado, set()):
        raise ValueError(f"Transicion invalida: {contract.estado} -> {new_status}")

    previous_status = contract.estado
    contract.estado = new_status
    if timestamp_field:
        setattr(contract, timestamp_field, datetime.utcnow())
    event_type = _event_type_for_status(new_status)
    event = None
    if event_type:
        event = ContractEvent(
            contract_id=contract.id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            previous_status=previous_status,
            new_status=new_status,
        )
        db.session.add(event)
        db.session.flush()
        target_user_id = (
            contract.cliente_id
            if actor_user_id == contract.professional_user_id
            else contract.professional_user_id
        )
        db.session.add(
            AuditLog(
                actor_user_id=actor_user_id,
                target_user_id=target_user_id,
                action=event_type,
                description=f"Contratacion #{contract.id}: {previous_status} -> {new_status}.",
                entity_type="ContractRequest",
                entity_id=contract.id,
                contract_id=contract.id,
                event_id=event.id,
                idempotency_key=f"contract:{contract.id}:{event_type}",
            )
        )
    db.session.commit()

    return contract


def accept_contract(contract_id, professional_user_id):
    _require_actor(professional_user_id)
    contract = get_contract_by_id(contract_id)
    if contract is None:
        return None
    _validate_professional_assignment(contract, professional_user_id)
    return _transition_contract(contract, "ACEPTADA", "accepted_at", actor_user_id=professional_user_id)


def reject_contract(contract_id, professional_user_id):
    _require_actor(professional_user_id)
    contract = get_contract_by_id(contract_id)
    if contract is None:
        return None
    _validate_professional_assignment(contract, professional_user_id)
    return _transition_contract(contract, "RECHAZADA", actor_user_id=professional_user_id)


def start_contract(contract_id, actor_user_id):
    contract = get_contract_by_id(contract_id)
    if contract is None:
        return None
    _validate_professional_assignment(contract, actor_user_id)
    return _transition_contract(contract, "EN_PROGRESO", "started_at", actor_user_id=actor_user_id)


def complete_contract(contract_id, actor_user_id):
    contract = get_contract_by_id(contract_id)
    if contract is None:
        return None
    _validate_professional_assignment(contract, actor_user_id)
    return _transition_contract(contract, "COMPLETADA", "completed_at", actor_user_id=actor_user_id)


def confirm_contract(contract_id, actor_user_id):
    contract = get_contract_by_id(contract_id)
    if contract is None:
        return None
    require_client_owner(contract, actor_user_id)
    return _transition_contract(contract, "CONFIRMADA", "confirmed_at", actor_user_id=actor_user_id)


def cancel_contract(contract_id, actor_user_id):
    contract = get_contract_by_id(contract_id)
    if contract is None:
        return None
    require_client_owner(contract, actor_user_id)
    return _transition_contract(contract, "CANCELADA", "cancelled_at", actor_user_id=actor_user_id)


def update_contract_status(contract_id, estado):
    if estado not in ContractRequest.ESTADOS:
        raise ValueError("Estado de contrato invalido")

    contract = get_contract_by_id(contract_id)
    if contract is None:
        return None

    return _transition_contract(contract, estado)
