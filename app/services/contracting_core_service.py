from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from app import db
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.budget_offer import BudgetOffer
from app.models.contract_event import ContractEvent
from app.models.contract_request import ContractRequest
from app.models.proposal_application import ProposalApplication
from app.services.actor_policy_service import require_active_actor
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
    "contract_version",
}

__all__ = (
    "ContractCreationResult",
    "create_contract_from_budget_offer",
    "create_contract_from_proposal_application",
)


def _safe_metadata(data, allowed_keys=SOURCE_METADATA_KEYS):
    return {
        key: value
        for key, value in (data or {}).items()
        if key in allowed_keys and isinstance(value, (str, int, float, bool, type(None)))
    }


def _add_audit_log(
    actor_user_id,
    action,
    target_user_id=None,
    description="",
    contract_id=None,
    event_id=None,
    idempotency_key=None,
    correlation_id=None,
    operation=None,
    metadata_json=None,
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
            correlation_id=correlation_id,
            operation=operation,
            idempotency_key=idempotency_key,
            metadata_json=_safe_metadata(metadata_json),
        )
    )


def _add_notification(
    user_id,
    actor_user_id,
    tipo,
    titulo,
    mensaje,
    url_destino,
    entity_id,
    event_id,
    correlation_id,
):
    db.session.add(
        ActivityNotification(
            user_id=user_id,
            actor_user_id=actor_user_id,
            contract_event_id=event_id,
            correlation_id=correlation_id,
            idempotency_key=f"notification:{event_id}:{user_id}:{tipo}:INTERNAL",
            template_key=tipo,
            channel="INTERNAL",
            delivery_status="DELIVERED",
            attempt_count=0,
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


def _notify_contract_created(
    contract,
    actor_user_id,
    professional_message,
    event_id,
    correlation_id,
):
    url = f"/contratacion/{contract.id}"
    _add_notification(
        user_id=contract.cliente_id,
        actor_user_id=actor_user_id,
        tipo="CONTRACT_CREATED",
        titulo="Se creo una contratacion",
        mensaje=f"La contratacion para {contract.servicio} quedo registrada.",
        url_destino=url,
        entity_id=contract.id,
        event_id=event_id,
        correlation_id=correlation_id,
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
            event_id=event_id,
            correlation_id=correlation_id,
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
    professional_message,
    budget_offer_id=None,
    proposal_application_id=None,
):
    expected_source_event = {
        ContractRequest.SOURCE_BUDGET: ContractEvent.CREATED_FROM_BUDGET,
        ContractRequest.SOURCE_PROPOSAL: ContractEvent.CREATED_FROM_PROPOSAL,
    }.get(source_type)
    if expected_source_event is None or created_from_event != expected_source_event:
        raise ValueError("Origen contractual derivado invalido")
    if actor_user_id is None:
        raise PermissionError("Actor requerido para eventos contractuales derivados")

    correlation_id = str(uuid4())
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
        contracting_mode=ContractRequest.CONTRACTING_MODE_EXTERNAL,
        version=1,
    )
    db.session.add(contract)
    db.session.flush()

    created_event = ContractEvent(
        contract_id=contract.id,
        event_type=ContractEvent.CONTRACT_CREATED,
        actor_user_id=actor_user_id,
        sequence_no=1,
        correlation_id=correlation_id,
        idempotency_key=f"event:contract:{source_type}:{source_id}:created",
        previous_status=None,
        new_status=contract.estado,
        metadata_json={
            "source_type": source_type,
            "source_id": source_id,
            "budget_offer_id": budget_offer_id,
            "proposal_application_id": proposal_application_id,
            "contract_version": contract.version,
        },
    )
    db.session.add(created_event)
    db.session.flush()
    source_event = ContractEvent(
        contract_id=contract.id,
        event_type=expected_source_event,
        actor_user_id=actor_user_id,
        sequence_no=2,
        correlation_id=correlation_id,
        causation_event_id=created_event.id,
        idempotency_key=f"event:contract:{source_type}:{source_id}:source",
        previous_status=None,
        new_status=contract.estado,
        metadata_json={"source_type": source_type, "source_id": source_id},
    )
    db.session.add(source_event)
    db.session.flush()
    _add_audit_log(
        actor_user_id=actor_user_id,
        target_user_id=professional_user_id,
        action=created_from_event,
        description=f"Contrato #{contract.id} creado desde {source_type}.",
        contract_id=contract.id,
        event_id=source_event.id or created_event.id,
        idempotency_key=f"contract:{source_type}:{source_id}",
        correlation_id=correlation_id,
        operation=created_from_event,
        metadata_json={
            "source_type": source_type,
            "source_id": source_id,
            "contract_version": contract.version,
        },
    )
    _notify_contract_created(
        contract,
        actor_user_id,
        professional_message,
        event_id=source_event.id,
        correlation_id=correlation_id,
    )

    return contract


def _budget_contract(offer_id):
    return ContractRequest.query.filter_by(budget_offer_id=offer_id).first()


def _proposal_contract(application_id):
    return ContractRequest.query.filter_by(
        proposal_application_id=application_id
    ).first()


def create_contract_from_budget_offer(offer_id, *, actor_user_id):
    actor = require_active_actor(actor_user_id, ("CLIENTE",))
    offer = BudgetOffer.query.filter_by(id=offer_id).with_for_update().first()
    if offer is None:
        raise ValueError("Presupuesto adjudicado no encontrado")

    budget_request = offer.budget_request
    if budget_request.cliente_id != actor.id:
        raise PermissionError("Solo el cliente dueno puede crear la contratacion")
    if offer.estado != "ADJUDICADO":
        raise ValueError("Solo una oferta adjudicada puede crear una contratacion")

    existing = _budget_contract(offer.id)
    if existing is not None:
        return ContractCreationResult(existing, created=False)

    try:
        with db.session.begin_nested():
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
                actor_user_id=actor.id,
                professional_message=(
                    f"El cliente adjudico tu presupuesto para "
                    f"{budget_request.titulo}. Debes aceptar o rechazar la contratacion."
                ),
            )
    except IntegrityError:
        existing = _budget_contract(offer.id)
        if existing is None:
            raise
        return ContractCreationResult(existing, created=False)

    return ContractCreationResult(contract, created=True, state_changed=True)


def create_contract_from_proposal_application(application_id, *, actor_user_id):
    actor = require_active_actor(actor_user_id, ("CLIENTE",))
    application = ProposalApplication.query.filter_by(id=application_id).with_for_update().first()
    if application is None:
        raise ValueError("Postulacion aceptada no encontrada")

    proposal = application.proposal
    owner_id = proposal.owner_user_id or proposal.cliente_id
    if owner_id != actor.id:
        raise PermissionError("Solo el publicador puede crear la contratacion")
    if proposal.hiring_mode != "SINGLE":
        raise ValueError("hiring_mode MULTIPLE queda diferido a la Fase 2C")
    if application.estado != "ACEPTADA":
        raise ValueError("Solo una postulacion aceptada puede crear una contratacion")

    existing = _proposal_contract(application.id)
    if existing is not None:
        return ContractCreationResult(existing, created=False)

    try:
        with db.session.begin_nested():
            contract = _create_contract(
                cliente_id=owner_id,
                professional_id=application.professional_id,
                professional_user_id=application.professional_user_id,
                servicio=proposal.titulo or proposal.categoria,
                descripcion=application.mensaje or proposal.descripcion,
                precio_acordado=application.pretension_economica
                or proposal.presupuesto_estimado,
                source_type=ContractRequest.SOURCE_PROPOSAL,
                source_id=application.id,
                budget_offer_id=None,
                proposal_application_id=application.id,
                created_from_event=ContractEvent.CREATED_FROM_PROPOSAL,
                actor_user_id=actor.id,
                professional_message=(
                    f"El publicador acepto tu postulacion para "
                    f"{proposal.titulo or proposal.categoria}. "
                    "Debes aceptar o rechazar la contratacion."
                ),
            )
    except IntegrityError:
        existing = _proposal_contract(application.id)
        if existing is None:
            raise
        return ContractCreationResult(existing, created=False)

    return ContractCreationResult(contract, created=True, state_changed=True)
