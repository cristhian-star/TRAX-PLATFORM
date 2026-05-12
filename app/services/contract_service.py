from app import db
from app.models.contract_request import ContractRequest


def create_contract(
    cliente_id,
    professional_id,
    servicio,
    descripcion=None,
    precio_acordado=None,
    fecha_inicio=None,
    fecha_fin=None
):
    contract = ContractRequest(
        cliente_id=cliente_id,
        professional_id=professional_id,
        servicio=servicio,
        descripcion=descripcion,
        precio_acordado=precio_acordado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
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


def update_contract_status(contract_id, estado):
    if estado not in ContractRequest.ESTADOS:
        raise ValueError("Estado de contrato invalido")

    contract = get_contract_by_id(contract_id)

    if contract is None:
        return None

    contract.estado = estado
    db.session.commit()

    return contract
