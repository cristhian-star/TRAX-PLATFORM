import re

from app import db
from app.services.proposal_eligibility_service import proposal_application_eligibility
from app.models.professional import Professional
from app.models.user import User
from app.models.contract_request import ContractRequest
from app.services.budget_service import (
    MAX_OFFERS_PER_REQUEST,
    get_budget_offers,
    get_client_budget_requests_with_counts,
    get_offer_allowance,
    get_professional_budget_offers,
)
from app.services.geographic_matching_service import obtener_resultado_cobertura
from app.services.professional_service import search_emergency_professionals
from app.services.proposal_service import (
    get_professional_application,
    get_proposal_applications,
)
from app.services.review_service import (
    get_professional_average_rating,
    get_professional_reviews,
)
from app.services.subscription_service import has_pro_access
from app.services.taxonomy_service import (
    obtener_categorias,
    obtener_especialidades,
    obtener_industrias,
    obtener_rubros,
)
from app.services.verification_service import has_approved_verification


def build_emergency_professional_data(professional, coordinates=None):
    user_id = professional.user_id
    phone_digits = re.sub(r"\D", "", professional.telefono or "")
    is_pro = has_pro_access(user_id) if user_id else False
    is_verified = has_approved_verification(user_id) if user_id else False
    reviews = get_professional_reviews(professional.id)
    average_rating = get_professional_average_rating(professional.id)
    latitude = coordinates[0] if coordinates is not None else None
    longitude = coordinates[1] if coordinates is not None else None
    coverage_match = obtener_resultado_cobertura(professional, latitude, longitude)

    return {
        "professional": professional,
        "badges": {
            "work": True,
            "pro": is_pro,
            "verified": is_verified,
        },
        "rating": {
            "average": average_rating,
            "count": len(reviews),
        },
        "phone": {
            "whatsapp": bool(phone_digits),
            "call": None,
        },
        "availability": {
            "primary": "Disponibilidad por confirmar",
            "secondary": "Consultá antes de coordinar una visita",
            "priority": None,
        },
        "coverage_match": coverage_match,
        "sort": {
            "coverage": coverage_match["sort_rank"],
            "pro": 1 if is_pro else 0,
            "verified": 1 if is_verified else 0,
            "rating": average_rating or 0,
            "distance": coverage_match["distance_km"],
        },
    }


def build_emergency_directory_rows(categoria, zona, coordinates):
    professionals = search_emergency_professionals(categoria, zona)
    return sorted(
        (build_emergency_professional_data(professional, coordinates) for professional in professionals),
        key=lambda row: (
            row["sort"]["coverage"] if coordinates is not None else 0,
            -row["sort"]["verified"],
            -row["sort"]["rating"],
            row["sort"]["distance"]
            if coordinates is not None and row["sort"]["distance"] is not None
            else float("inf"),
            row["professional"].nombre.casefold(),
        ),
    )


def build_budget_offer_data(offer):
    professional = offer.professional
    reviews = get_professional_reviews(professional.id)
    user_id = professional.user_id
    phone_digits = re.sub(r"\D", "", professional.telefono or "")

    return {
        "offer": offer,
        "professional": professional,
        "badges": {
            "work": True,
            "pro": has_pro_access(user_id) if user_id else False,
            "verified": has_approved_verification(user_id) if user_id else False,
        },
        "rating": {
            "average": get_professional_average_rating(professional.id),
            "count": len(reviews),
        },
        "phone": {
            "whatsapp": bool(phone_digits),
        },
    }


def build_client_budget_request_rows(user_id, status_filter):
    statuses_by_filter = {
        "activas": ("ABIERTO", "PUBLICADA", "COTIZANDO"),
        "adjudicadas": ("ADJUDICADA",),
        "canceladas": ("CANCELADA",),
        "todas": None,
    }
    normalized_filter = status_filter if status_filter in statuses_by_filter else "activas"
    request_rows = [
        {
            "budget_request": budget_request,
            "offer_count": offer_count,
        }
        for budget_request, offer_count in get_client_budget_requests_with_counts(
            user_id,
            estados=statuses_by_filter[normalized_filter],
        )
    ]

    return request_rows, normalized_filter


def budget_layout_context(user_id):
    user = db.session.get(User, user_id)
    professional_layout = bool(user and user.rol == "PROFESIONAL")
    if professional_layout:
        from app.services.professional_workspace_service import build_workspace
        return {"budget_workspace": True, "workspace": build_workspace(user_id)}
    return {"budget_workspace": False}


def budget_offer_status(offer, budget_request):
    if offer.estado == "ADJUDICADO":
        return "Adjudicado"
    return {"ADJUDICADA": "Otra oferta fue adjudicada", "CANCELADA": "Solicitud cancelada",
            "CERRADA": "Solicitud cerrada"}.get(budget_request.estado, "En espera de decisión")


def build_professional_budget_offer_rows(user_id):
    offer_rows = []

    for offer in get_professional_budget_offers(user_id):
        budget_request = offer.budget_request
        client = db.session.get(User, budget_request.cliente_id)
        offer_rows.append({
            "offer": offer,
            "budget_request": budget_request,
            "client": client,
            "status_label": budget_offer_status(offer, budget_request),
            "offer_count": len(budget_request.offers),
        })

    return offer_rows


def build_budget_detail_context(budget_request, current_user_id, query_args):
    current_user = db.session.get(User, current_user_id)
    is_owner = (
        current_user is not None
        and current_user.estado == "ACTIVO"
        and current_user.rol == "CLIENTE"
        and budget_request.cliente_id == current_user_id
    )
    current_professional = Professional.query.filter_by(user_id=current_user_id).first()
    is_professional = (
        current_user is not None
        and current_user.rol == "PROFESIONAL"
        and current_professional is not None
    )
    offers = get_budget_offers(budget_request.id)
    own_offer = next(
        (
            offer
            for offer in offers
            if offer.professional_user_id == current_user_id
        ),
        None,
    )

    return {
        "budget_request": budget_request,
        "offer_rows": [build_budget_offer_data(offer) for offer in offers] if is_owner else [],
        "offer_count": len(offers),
        "max_offers": MAX_OFFERS_PER_REQUEST,
        "is_owner": is_owner,
        "budget_contract": (
            ContractRequest.query.filter(
                ContractRequest.cliente_id == current_user_id,
                ContractRequest.source_type == ContractRequest.SOURCE_BUDGET,
                ContractRequest.budget_offer_id.in_([offer.id for offer in offers]),
            ).first() if is_owner else (
                ContractRequest.query.filter_by(
                    source_type=ContractRequest.SOURCE_BUDGET,
                    budget_offer_id=own_offer.id,
                    professional_user_id=current_user_id,
                    professional_id=current_professional.id,
                ).first() if own_offer and is_professional and own_offer.estado == "ADJUDICADO" else None
            )
        ),
        "is_professional": is_professional,
        "own_offer": own_offer,
        "own_offer_status": budget_offer_status(own_offer, budget_request) if own_offer else None,
        "profile_ready": bool(current_professional and current_professional.perfil_completo),
        "offer_allowance": get_offer_allowance(current_user_id) if is_professional else None,
        "offer_error": query_args.get("error"),
        "offer_sent": query_args.get("enviado") == "1" and own_offer is not None,
        "awarded": query_args.get("adjudicado") == "1" and is_owner and budget_request.estado == "ADJUDICADA",
    }


def build_proposal_taxonomy_options(include_specialties=True):
    taxonomy = {
        "industrias": obtener_industrias(),
        "categorias": obtener_categorias(),
        "rubros": obtener_rubros(),
    }
    if include_specialties:
        taxonomy["especialidades"] = obtener_especialidades()

    return taxonomy


def build_proposal_detail_context(proposal, current_user_id, query_args):
    current_user = db.session.get(User, current_user_id) if current_user_id else None
    is_owner = current_user_id is not None and (proposal.owner_user_id or proposal.cliente_id) == current_user_id
    current_professional = Professional.query.filter_by(user_id=current_user_id).first() if current_user_id else None
    is_professional = current_user is not None and current_user.rol == "PROFESIONAL" and current_professional is not None
    own_application = (
        get_professional_application(proposal.id, current_user_id)
        if is_professional
        else None
    )
    applications = get_proposal_applications(proposal.id) if is_owner else []
    owner = db.session.get(User, proposal.owner_user_id or proposal.cliente_id)

    return {
        "proposal": proposal,
        "owner": owner,
        "applications": applications,
        "is_owner": is_owner,
        "is_professional": is_professional,
        "application_eligibility": proposal_application_eligibility(current_user_id),
        "own_application": own_application,
        "current_user": current_user,
        "error": query_args.get("error"),
        "applied": query_args.get("postulada") == "1",
        "published": query_args.get("publicada") == "1",
    }
def budget_publication_age(created_at, now=None):
    """Relative age of the existing naive-UTC publication timestamp."""
    from datetime import datetime
    elapsed = max(0, int(((now or datetime.utcnow()) - created_at).total_seconds()))
    if elapsed >= 86400:
        days = elapsed // 86400
        return f"Hace {days} {'día' if days == 1 else 'días'}"
    if elapsed >= 3600:
        return f"Hace {elapsed // 3600} h"
    if elapsed >= 60:
        return f"Hace {elapsed // 60} min"
    return "Recién publicada"
