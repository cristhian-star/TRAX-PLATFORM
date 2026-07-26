from dataclasses import dataclass

from app import db
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.budget_offer import BudgetOffer
from app.models.contract_event import ContractEvent
from app.models.contract_request import ContractRequest
from app.models.proposal_application import ProposalApplication
from app.services.notification_service import (
    CATEGORIA_CONTRATACIONES,
    PRIORIDAD_ACCION_REQUERIDA,
)


@dataclass(frozen=True)
class ContractCreationResult:
    contract: ContractRequest
    created: bool
    state_changed: bool = False


SOURCE_METADATA_KEYS = {
    "source_type",
    "source_id",
    "budget_offer_id",
    "proposal_application_id",
}


def _safe_metadata(data, allowed_keys=SOURCE_METADATA_KEYS):
    return {
        key: value
        for key, value in (data or {}).items()
        if key in allowed_keys and isinstance(value, (str, int, float, bool, type(None)))
    }


def create_contract_event(
    contract,
    event_type,
    actor_user_id=None,
    previous_status=None,
    new_status=None,
    metadata_json=None,
):
    if event_type not in ContractEvent.EVENT_TYPES:
        raise ValueError("Tipo de evento de contrato invalido")

    event = ContractEvent(
        contract=contract,
        event_type=event_type,
        actor_user_id=actor_user_id,
        previous_status=previous_status,
        new_status=new_status,
        metadata_json=_safe_metadata(metadata_json),
    )
    db.session.add(event)
    db.session.flush()
    return event


def _add_audit_log(
    actor_user_id,
    action,
    target_user_id=None,
    description="",
    contract_id=None,
    event_id=None,
    idempotency_key=None,
):
    db.session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            action=action,
            description=description,
            entity_type="ContractRequest" if contract_id else None,
            entity_id=contract_id,
            contract_id=contract_id,
            event_id=event_id,
            idempotency_key=idempotency_key,
        )
    )


def _add_notification(user_id, actor_user_id, tipo, titulo, mensaje, url_destino, entity_id):
    db.session.add(
        ActivityNotification(
            user_id=user_id,
            actor_user_id=actor_user_id,
            tipo=tipo,
            categoria=CATEGORIA_CONTRATACIONES,
            titulo=titulo,
            mensaje=mensaje,
            url_destino=url_destino,
            entity_type="ContractRequest",
            entity_id=entity_id,
            prioridad=PRIORIDAD_ACCION_REQUERIDA,
            requiere_accion=True,
        )
    )


def _notify_contract_created(contract, actor_user_id, professional_message):
    url = f"/contratacion/{contract.id}"
    _add_notification(
        user_id=contract.cliente_id,
        actor_user_id=actor_user_id,
        tipo="CONTRACT_CREATED",
        titulo="Se creo una contratacion",
        mensaje=f"La contratacion para {contract.servicio} quedo registrada.",
        url_destino=url,
        entity_id=contract.id,
    )
    if contract.professional_user_id:
        _add_notification(
            user_id=contract.professional_user_id,
            actor_user_id=actor_user_id,
            tipo="CONTRACT_CREATED",
            titulo="Tenes una contratacion pendiente",
            mensaje=professional_message,
            url_destino=url,
            entity_id=contract.id,
        )


def _create_contract(
    cliente_id,
    professional_id,
    professional_user_id,
    servicio,
    descripcion,
    precio_acordado,
    source_type,
    source_id,
    created_from_event,
    actor_user_id,
    budget_offer_id=None,
    proposal_application_id=None,
):
    contract = ContractRequest(
        cliente_id=cliente_id,
        professional_id=professional_id,
        professional_user_id=professional_user_id,
        servicio=servicio,
        descripcion=descripcion,
        precio_acordado=precio_acordado,
        source_type=source_type,
        source_id=source_id,
        budget_offer_id=budget_offer_id,
        proposal_application_id=proposal_application_id,
        created_from_event=created_from_event,
        estado="CREADA",
    )
    db.session.add(contract)
    db.session.flush()

    created_event = create_contract_event(
        contract,
        ContractEvent.CONTRACT_CREATED,
        actor_user_id=actor_user_id,
        new_status=contract.estado,
        metadata_json={
            "source_type": source_type,
            "source_id": source_id,
            "budget_offer_id": budget_offer_id,
            "proposal_application_id": proposal_application_id,
        },
    )
    source_event = create_contract_event(
        contract,
        created_from_event,
        actor_user_id=actor_user_id,
        new_status=contract.estado,
        metadata_json={"source_type": source_type, "source_id": source_id},
    )
    _add_audit_log(
        actor_user_id=actor_user_id,
        target_user_id=professional_user_id,
        action=created_from_event,
        description=f"Contrato #{contract.id} creado desde {source_type}.",
        contract_id=contract.id,
        event_id=source_event.id or created_event.id,
        idempotency_key=f"contract:{source_type}:{source_id}",
    )

    return contract


def _require_actor(actor_user_id):
    if actor_user_id is None:
        raise PermissionError("Actor requerido para crear contrataciones derivadas")


def create_contract_from_budget_offer(offer_id, actor_user_id=None):
    _require_actor(actor_user_id)
    existing = ContractRequest.query.filter_by(budget_offer_id=offer_id).first()
    if existing is not None:
        if existing.cliente_id != actor_user_id:
            raise PermissionError("Solo el cliente dueno puede consultar esta contratacion")
        return ContractCreationResult(existing, created=False)

    offer = BudgetOffer.query.filter_by(id=offer_id).with_for_update().first()
    if offer is None:
        raise ValueError("Presupuesto adjudicado no encontrado")
    if offer.estado != "ADJUDICADO":
        raise ValueError("Solo una oferta adjudicada puede crear una contratacion")

    budget_request = offer.budget_request
    if budget_request.cliente_id != actor_user_id:
        raise PermissionError("Solo el cliente dueno puede crear la contratacion")

    contract = _create_contract(
        cliente_id=budget_request.cliente_id,
        professional_id=offer.professional_id,
        professional_user_id=offer.professional_user_id,
        servicio=budget_request.titulo or budget_request.categoria,
        descripcion=offer.condiciones or budget_request.descripcion,
        precio_acordado=offer.monto_desde or offer.monto,
        source_type=ContractRequest.SOURCE_BUDGET,
        source_id=offer.id,
        budget_offer_id=offer.id,
        proposal_application_id=None,
        created_from_event=ContractEvent.CREATED_FROM_BUDGET,
        actor_user_id=actor_user_id or budget_request.cliente_id,
    )
    _notify_contract_created(
        contract,
        actor_user_id or budget_request.cliente_id,
        f"El cliente adjudico tu presupuesto para {budget_request.titulo}. Debes aceptar o rechazar la contratacion.",
    )
    return ContractCreationResult(contract, created=True, state_changed=True)


def create_contract_from_proposal_application(application_id, actor_user_id=None):
    _require_actor(actor_user_id)
    existing = ContractRequest.query.filter_by(proposal_application_id=application_id).first()
    if existing is not None:
        if existing.cliente_id != actor_user_id:
            raise PermissionError("Solo el publicador puede consultar esta contratacion")
        return ContractCreationResult(existing, created=False)

    application = ProposalApplication.query.filter_by(id=application_id).with_for_update().first()
    if application is None:
        raise ValueError("Postulacion aceptada no encontrada")
    if application.estado != "ACEPTADA":
        raise ValueError("Solo una postulacion aceptada puede crear una contratacion")

    proposal = application.proposal
    owner_id = proposal.owner_user_id or proposal.cliente_id
    if owner_id != actor_user_id:
        raise PermissionError("Solo el publicador puede crear la contratacion")

    contract = _create_contract(
        cliente_id=owner_id,
        professional_id=application.professional_id,
        professional_user_id=application.professional_user_id,
        servicio=proposal.titulo or proposal.categoria,
        descripcion=application.mensaje or proposal.descripcion,
        precio_acordado=application.pretension_economica or proposal.presupuesto_estimado,
        source_type=ContractRequest.SOURCE_PROPOSAL,
        source_id=application.id,
        budget_offer_id=None,
        proposal_application_id=application.id,
        created_from_event=ContractEvent.CREATED_FROM_PROPOSAL,
        actor_user_id=actor_user_id or owner_id,
    )
    _notify_contract_created(
        contract,
        actor_user_id or owner_id,
        f"El publicador acepto tu postulacion para {proposal.titulo or proposal.categoria}. Debes aceptar o rechazar la contratacion.",
    )
    return ContractCreationResult(contract, created=True, state_changed=True)
