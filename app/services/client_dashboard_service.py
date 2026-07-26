from app.models.contract_request import ContractRequest
from app.models.emergency_request import EmergencyRequest
from app.models.proposal_request import ProposalRequest
from app.models.user import User
from app.services.budget_service import get_client_budget_requests_with_counts
from app.services.notification_service import (
    formatear_fecha_notificacion,
    obtener_notificaciones_usuario,
)
from app.services.whatsapp_contact_service import obtener_contactos_cliente


def format_dashboard_date(value):
    if not value:
        return "Sin fecha"

    return value.strftime("%d/%m/%Y")


def build_client_activity_rows(budget_rows, emergency_requests, proposal_requests, contracts):
    activity_rows = []

    for row in budget_rows:
        budget_request = row.BudgetRequest if hasattr(row, "BudgetRequest") else row[0]
        offer_count = row.offer_count if hasattr(row, "offer_count") else row[1]
        activity_rows.append({
            "kind": "Presupuesto",
            "title": f"Publicaste: {budget_request.titulo}",
            "detail": f"{offer_count} presupuestos recibidos - Estado {budget_request.estado}",
            "date": budget_request.fecha_creacion,
            "href": f"/presupuestos/{budget_request.id}",
        })

        awarded_offers = [
            offer for offer in budget_request.offers if offer.estado == "ADJUDICADO"
        ]
        for offer in awarded_offers:
            professional_name = (
                offer.professional.nombre
                if offer.professional and offer.professional.nombre
                else "Profesional adjudicado"
            )
            activity_rows.append({
                "kind": "Adjudicacion",
                "title": f"Adjudicaste a {professional_name}",
                "detail": budget_request.titulo,
                "date": offer.fecha_creacion,
                "href": f"/presupuestos/{budget_request.id}",
            })

    for emergency in emergency_requests:
        activity_rows.append({
            "kind": "Emergencia",
            "title": f"Publicaste una emergencia de {emergency.categoria}",
            "detail": f"{emergency.zona} - Estado {emergency.estado}",
            "date": emergency.fecha_creacion,
            "href": "/emergencias/nueva",
        })

    for proposal in proposal_requests:
        activity_rows.append({
            "kind": "Propuesta",
            "title": f"Publicaste: {proposal.titulo or proposal.categoria}",
            "detail": f"{len(proposal.applications)} postulaciones - Estado {proposal.estado}",
            "date": proposal.created_at,
            "href": f"/propuestas/{proposal.id}",
        })

        accepted_applications = [
            application for application in proposal.applications if application.estado == "ACEPTADA"
        ]
        for application in accepted_applications:
            professional_name = (
                application.professional.nombre
                if application.professional and application.professional.nombre
                else "Profesional aceptado"
            )
            activity_rows.append({
                "kind": "Adjudicacion",
                "title": f"Aceptaste a {professional_name}",
                "detail": proposal.titulo or proposal.categoria,
                "date": application.created_at,
                "href": f"/propuestas/{proposal.id}",
            })

    for contract in contracts:
        activity_rows.append({
            "kind": "Contratacion",
            "title": f"Contratacion: {contract.servicio}",
            "detail": f"Estado {contract.estado}",
            "date": contract.fecha_creacion,
            "href": f"/contratacion/{contract.id}",
        })

    return sorted(
        activity_rows,
        key=lambda item: item["date"].timestamp() if item["date"] else 0,
        reverse=True,
    )[:8]


def count_unique_awarded_professionals(budget_rows, proposal_requests, contracts):
    awarded_professionals = set()

    for row in budget_rows:
        budget_request = row.BudgetRequest if hasattr(row, "BudgetRequest") else row[0]
        for offer in budget_request.offers:
            if offer.estado == "ADJUDICADO":
                awarded_professionals.add(("budget", offer.professional_user_id))

    for proposal in proposal_requests:
        for application in proposal.applications:
            if application.estado == "ACEPTADA":
                awarded_professionals.add(("proposal", application.professional_user_id))

    for contract in contracts:
        if contract.professional_user_id:
            awarded_professionals.add(("contract_user", contract.professional_user_id))
        elif contract.professional_id:
            awarded_professionals.add(("contract_profile", contract.professional_id))

    return len(awarded_professionals)


def build_client_dashboard_context(user_id):
    current_user = User.query.get(user_id)
    budget_rows = get_client_budget_requests_with_counts(user_id)
    budget_requests = [
        row.BudgetRequest if hasattr(row, "BudgetRequest") else row[0]
        for row in budget_rows
    ]
    emergency_requests = (
        EmergencyRequest.query
        .filter_by(cliente_id=user_id)
        .order_by(EmergencyRequest.fecha_creacion.desc(), EmergencyRequest.id.desc())
        .all()
    )
    proposal_requests = (
        ProposalRequest.query
        .filter_by(cliente_id=user_id)
        .order_by(ProposalRequest.created_at.desc(), ProposalRequest.id.desc())
        .all()
    )
    contracts = (
        ContractRequest.query
        .filter_by(cliente_id=user_id)
        .order_by(ContractRequest.fecha_creacion.desc(), ContractRequest.id.desc())
        .all()
    )

    active_budget_count = len([
        request_item for request_item in budget_requests
        if request_item.estado in ("ABIERTO", "PUBLICADA", "COTIZANDO")
    ])
    active_emergency_count = len([
        request_item for request_item in emergency_requests
        if request_item.estado in ("ABIERTA", "ASIGNADA", "EN_CAMINO")
    ])
    active_proposal_count = len([
        request_item for request_item in proposal_requests
        if request_item.estado == "PUBLICADA"
    ])
    total_offer_count = sum(
        row.offer_count if hasattr(row, "offer_count") else row[1]
        for row in budget_rows
    )
    total_application_count = sum(
        len(proposal.applications) for proposal in proposal_requests
    )
    awarded_professionals_count = count_unique_awarded_professionals(
        budget_rows,
        proposal_requests,
        contracts,
    )
    history_count = (
        len(budget_requests)
        + len(emergency_requests)
        + len(proposal_requests)
        + len(contracts)
    )
    latest_dates = [
        value
        for value in [
            *(request_item.fecha_creacion for request_item in budget_requests),
            *(request_item.fecha_creacion for request_item in emergency_requests),
            *(request_item.created_at for request_item in proposal_requests),
            *(contract.fecha_creacion for contract in contracts),
        ]
        if value
    ]
    latest_activity = max(latest_dates) if latest_dates else None

    recommendations = []
    if not budget_requests:
        recommendations.append({
            "title": "Publicar un presupuesto",
            "detail": "Crea tu primera solicitud para comparar respuestas profesionales.",
            "href": "/presupuestos/nuevo",
        })
    if not emergency_requests:
        recommendations.append({
            "title": "Preparar una emergencia",
            "detail": "Conoce el flujo urgente antes de necesitarlo.",
            "href": "/emergencias/nueva",
        })
    if not proposal_requests:
        recommendations.append({
            "title": "Publicar una propuesta",
            "detail": "Usa propuestas para proyectos que requieren postulaciones.",
            "href": "/propuestas/nueva",
        })
    recommendations.extend([
        {
            "title": "Explorar profesionales",
            "detail": "Busca perfiles por rubro, zona y reputacion.",
            "href": "/explorar",
        },
        {
            "title": "Invitar profesionales",
            "detail": "Comparte tus solicitudes con perfiles compatibles cuando tengas el enlace.",
            "href": "/resultados",
        },
    ])

    request_sections = [
        {
            "title": "Presupuestos",
            "count": len(budget_requests),
            "active_count": active_budget_count,
            "items": budget_requests[:3],
            "href": "/presupuestos/mis-solicitudes",
            "empty": "Todavia no publicaste solicitudes de presupuesto.",
        },
        {
            "title": "Emergencias",
            "count": len(emergency_requests),
            "active_count": active_emergency_count,
            "items": emergency_requests[:3],
            "href": "/emergencias/nueva",
            "empty": "Todavia no registraste emergencias.",
        },
        {
            "title": "Propuestas",
            "count": len(proposal_requests),
            "active_count": active_proposal_count,
            "items": proposal_requests[:3],
            "href": "/propuestas",
            "empty": "Todavia no publicaste propuestas.",
        },
    ]

    return {
        "current_user": current_user,
        "last_access": None,
        "activity_rows": build_client_activity_rows(
            budget_rows,
            emergency_requests,
            proposal_requests,
            contracts,
        ),
        "active_budget_count": active_budget_count,
        "active_emergency_count": active_emergency_count,
        "active_proposal_count": active_proposal_count,
        "awarded_professionals_count": awarded_professionals_count,
        "history_count": history_count,
        "total_offer_count": total_offer_count,
        "total_application_count": total_application_count,
        "total_request_count": history_count,
        "latest_activity": latest_activity,
        "request_sections": request_sections,
        "recommendations": recommendations[:5],
        "whatsapp_contact_sessions": obtener_contactos_cliente(user_id, limit=5),
        "format_dashboard_date": format_dashboard_date,
        "recent_activity": obtener_notificaciones_usuario(user_id, limit=5),
        "format_notification_date": formatear_fecha_notificacion,
    }
