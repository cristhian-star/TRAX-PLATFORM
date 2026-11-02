"""Read-only professional presentation; canonical evaluators own eligibility."""
from flask import abort
from sqlalchemy.orm import joinedload

from app.models.user import User
from app.models.professional import Professional
from app.models.contract_request import ContractRequest
from app.models.proposal_application import ProposalApplication
from app.services.professional_view_service import calculate_private_profile_completion, get_professional_rating
from app.services.professional_media_service import build_professional_media_context
from app.services.subscription_service import has_pro_access
from app.services.verification_service import has_approved_verification
from app.services.coverage_service import obtener_cobertura_profesional
from app.services.notification_service import obtener_notificaciones_usuario, present_notification
from app.services.budget_service import open_budget_requests_query, get_offer_allowance
from app.services.proposal_service import open_proposals_query
from app.services.proposal_eligibility_service import proposal_application_eligibility
from app.services.whatsapp_contact_service import obtener_contactos_profesional


def build_workspace(user_id):
    user = User.query.get(user_id)
    professional = Professional.query.filter_by(user_id=user_id).first()
    verified = has_approved_verification(user_id)
    rating = get_professional_rating(professional.id) if professional else dict(average=None, count=0)
    name = professional.nombre if professional else user.nombre
    return dict(professional=professional, name=name,
                initials="".join(word[0] for word in name.split()[:2]).upper(),
                verified=verified, plan="PRO" if has_pro_access(user_id) else "FREE",
                completion=calculate_private_profile_completion(professional, verified),
                rating=rating, coverage=obtener_cobertura_profesional(professional),
                media=build_professional_media_context(professional),
                public_url=f"/profesional/{professional.id}" if professional else None,
                notifications=obtener_notificaciones_usuario(user_id))


def owned_contracts(user_id):
    # These FKs refer to different tables; require both persisted ownership links.
    return ContractRequest.query.join(Professional, ContractRequest.professional_id == Professional.id).filter(
        ContractRequest.professional_user_id == user_id, Professional.user_id == user_id)


def contract_card(contract):
    labels = {
        "CREADA": ("Pendiente de aceptación", "Revisar solicitud"),
        "ACEPTADA": ("Aceptado", "Revisar inicio"),
        "EN_PROGRESO": ("En progreso", "Ver trabajo"),
        "COMPLETADA": ("Esperando confirmación del cliente", "Ver trabajo"),
        "CORRECCION_SOLICITADA": ("Corrección solicitada", "Revisar corrección"),
        "CONFIRMADA": ("Confirmado", "Ver trabajo"),
        "RECHAZADA": ("Rechazado", "Ver detalle"),
        "CANCELADA": ("Cancelado", "Ver detalle"),
    }
    label, action = labels.get(contract.estado, (contract.estado, "Ver detalle"))
    return dict(title=contract.servicio, state=label, action=action,
                origin={"DIRECT": "Contratación directa", "BUDGET": "Presupuesto", "PROPOSAL": "Propuesta", "EMERGENCY": "Urgencia"}.get(contract.source_type, contract.source_type), url=f"/contratacion/{contract.id}")


def opportunity_cards(limit=2, categoria=None, zona=None):
    budgets = open_budget_requests_query(categoria, zona).limit(limit).all()
    proposals = open_proposals_query(rubro=categoria, ubicacion=zona).limit(limit).all()
    return [dict(title=b.titulo, kind="Solicitud de presupuesto", zone=b.zona,
                 tag=b.categoria, url=f"/presupuestos/{b.id}", action="Ver solicitud") for b in budgets] + [
        dict(title=p.titulo, kind="Propuesta", zone=p.ubicacion, tag=p.rubro,
             url=f"/propuestas/{p.id}", action="Ver propuesta") for p in proposals]


def workspace_home(user_id):
    contracts = owned_contracts(user_id).filter(
        ContractRequest.estado.notin_(ContractRequest.TERMINAL_STATES)).order_by(
            ContractRequest.fecha_creacion.desc(), ContractRequest.id.desc())
    return dict(jobs=[contract_card(c) for c in contracts.limit(3)],
                active_count=contracts.count(), opportunities=opportunity_cards(1),
                activity=[present_notification(n) for n in obtener_notificaciones_usuario(user_id, limit=3)])


def page_number(args):
    value = args.get("page", "1")
    if len(args.getlist("page")) > 1 or not value.isascii() or not value.isdecimal() or len(value) > 4:
        abort(400)
    page = int(value)
    if not 1 <= page <= 1000:
        abort(400)
    return page


def workspace_jobs(user_id, args):
    page = page_number(args)
    query = owned_contracts(user_id).order_by(ContractRequest.fecha_creacion.desc(), ContractRequest.id.desc())
    total = query.count()
    return dict(jobs=[contract_card(c) for c in query.offset((page-1)*20).limit(20)],
                page=page, has_next=page*20 < total)


def workspace_opportunities(user_id, args):
    # Full canonical marketplaces retain their independent filters and pagination.
    page = page_number(args)
    applications = ProposalApplication.query.options(joinedload(ProposalApplication.proposal)).filter_by(
        professional_user_id=user_id).order_by(ProposalApplication.created_at.desc(), ProposalApplication.id.desc())
    total = applications.count()
    professional = Professional.query.filter_by(user_id=user_id).first()
    contacts = obtener_contactos_profesional(professional.id, limit=5) if professional else []
    client_ids = {contact.client_user_id for contact in contacts if contact.client_user_id}
    names = dict(User.query.with_entities(User.id, User.nombre).filter(User.id.in_(client_ids)).all()) if client_ids else {}
    return dict(opportunities=opportunity_cards(3), allowance=get_offer_allowance(user_id),
                eligibility=proposal_application_eligibility(user_id),
                contacts=[dict(name=names.get(c.client_user_id, "Visitante MANDOBRA"),
                               operation=c.operation_type.replace("_", " ").title(),
                               state=c.status.replace("_", " ").title(), date=c.initiated_at) for c in contacts],
                applications=applications.offset((page-1)*20).limit(20).all(), page=page, has_next=page*20 < total)
