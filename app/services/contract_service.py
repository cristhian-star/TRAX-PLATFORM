from datetime import datetime

from app import db
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
        estado="CREADA",
    )

    db.session.add(contract)
    db.session.commit()

    return contract


def get_contract_by_id(contract_id):
    return ContractRequest.query.get(contract_id)


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


def _transition_contract(contract, new_status, timestamp_field=None):
    if new_status not in TRANSITIONS.get(contract.estado, set()):
        raise ValueError(f"Transicion invalida: {contract.estado} -> {new_status}")

    contract.estado = new_status
    if timestamp_field:
        setattr(contract, timestamp_field, datetime.utcnow())
    db.session.commit()

    return contract


def accept_contract(contract_id, professional_user_id):
    contract = get_contract_by_id(contract_id)
    if contract is None:
        return None
    _validate_professional_assignment(contract, professional_user_id)
    return _transition_contract(contract, "ACEPTADA", "accepted_at")


def reject_contract(contract_id, professional_user_id):
    contract = get_contract_by_id(contract_id)
    if contract is None:
        return None
    _validate_professional_assignment(contract, professional_user_id)
    return _transition_contract(contract, "RECHAZADA")


def start_contract(contract_id):
    contract = get_contract_by_id(contract_id)
    if contract is None:
        return None
    return _transition_contract(contract, "EN_PROGRESO", "started_at")


def complete_contract(contract_id):
    contract = get_contract_by_id(contract_id)
    if contract is None:
        return None
    return _transition_contract(contract, "COMPLETADA", "completed_at")


def confirm_contract(contract_id):
    contract = get_contract_by_id(contract_id)
    if contract is None:
        return None
    return _transition_contract(contract, "CONFIRMADA", "confirmed_at")


def cancel_contract(contract_id):
    contract = get_contract_by_id(contract_id)
    if contract is None:
        return None
    return _transition_contract(contract, "CANCELADA", "cancelled_at")


def update_contract_status(contract_id, estado):
    if estado not in ContractRequest.ESTADOS:
        raise ValueError("Estado de contrato invalido")

    contract = get_contract_by_id(contract_id)
    if contract is None:
        return None

    return _transition_contract(contract, estado)
