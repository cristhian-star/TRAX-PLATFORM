from app import db
from app.models.user import User
from app.services.notification_service import (
    CATEGORIA_EMERGENCIAS,
    CATEGORIA_PRESUPUESTOS,
    CATEGORIA_PROPUESTAS,
    PRIORIDAD_ACCION_REQUERIDA,
    PRIORIDAD_INFO,
    TIPO_EMERGENCIA_PUBLICADA,
    TIPO_PRESUPUESTO_ADJUDICADO_CLIENTE,
    TIPO_PRESUPUESTO_ADJUDICADO_PROFESIONAL,
    TIPO_PRESUPUESTO_CANCELADO,
    TIPO_PRESUPUESTO_OFERTA_ENVIADA,
    TIPO_PRESUPUESTO_OFERTA_RECIBIDA,
    TIPO_PRESUPUESTO_PUBLICADO,
    TIPO_PROPUESTA_CANCELADA,
    TIPO_PROPUESTA_POSTULACION_ACEPTADA,
    TIPO_PROPUESTA_POSTULACION_DESCARTADA,
    TIPO_PROPUESTA_POSTULACION_ENVIADA,
    TIPO_PROPUESTA_POSTULACION_RECIBIDA,
    TIPO_PROPUESTA_PUBLICADA,
    registrar_evento,
)


def user_display_name(user_id, fallback="Usuario MANDOBRA"):
    user = db.session.get(User, user_id) if user_id else None
    return user.nombre if user and user.nombre else fallback


def notify_budget_created(budget_request):
    registrar_evento(
        user_id=budget_request.cliente_id,
        actor_user_id=budget_request.cliente_id,
        tipo=TIPO_PRESUPUESTO_PUBLICADO,
        categoria=CATEGORIA_PRESUPUESTOS,
        titulo="Publicaste una solicitud de presupuesto",
        mensaje=f"{budget_request.titulo} quedo disponible para recibir ofertas.",
        url_destino=f"/presupuestos/{budget_request.id}",
        entity_type="BudgetRequest",
        entity_id=budget_request.id,
    )


def notify_budget_offer_created(offer):
    budget_request = offer.budget_request
    professional_name = user_display_name(offer.professional_user_id, "Un profesional")

    registrar_evento(
        user_id=offer.professional_user_id,
        actor_user_id=offer.professional_user_id,
        tipo=TIPO_PRESUPUESTO_OFERTA_ENVIADA,
        categoria=CATEGORIA_PRESUPUESTOS,
        titulo="Enviaste un presupuesto preliminar",
        mensaje=f"Tu oferta para {budget_request.titulo} quedo registrada.",
        url_destino=f"/presupuestos/{budget_request.id}",
        entity_type="BudgetOffer",
        entity_id=offer.id,
    )
    registrar_evento(
        user_id=budget_request.cliente_id,
        actor_user_id=offer.professional_user_id,
        tipo=TIPO_PRESUPUESTO_OFERTA_RECIBIDA,
        categoria=CATEGORIA_PRESUPUESTOS,
        titulo="Recibiste un nuevo presupuesto",
        mensaje=f"{professional_name} envio una oferta para {budget_request.titulo}.",
        url_destino=f"/presupuestos/{budget_request.id}",
        entity_type="BudgetOffer",
        entity_id=offer.id,
        prioridad=PRIORIDAD_ACCION_REQUERIDA,
        requiere_accion=True,
    )


def notify_budget_awarded(offer):
    budget_request = offer.budget_request
    professional_name = user_display_name(offer.professional_user_id, "el profesional")

    registrar_evento(
        user_id=budget_request.cliente_id,
        actor_user_id=budget_request.cliente_id,
        tipo=TIPO_PRESUPUESTO_ADJUDICADO_CLIENTE,
        categoria=CATEGORIA_PRESUPUESTOS,
        titulo="Adjudicaste una oferta",
        mensaje=f"Seleccionaste a {professional_name} para {budget_request.titulo}.",
        url_destino=f"/presupuestos/{budget_request.id}",
        entity_type="BudgetOffer",
        entity_id=offer.id,
    )
    registrar_evento(
        user_id=offer.professional_user_id,
        actor_user_id=budget_request.cliente_id,
        tipo=TIPO_PRESUPUESTO_ADJUDICADO_PROFESIONAL,
        categoria=CATEGORIA_PRESUPUESTOS,
        titulo="Tu presupuesto fue adjudicado",
        mensaje=f"Fuiste seleccionado para {budget_request.titulo}.",
        url_destino=f"/presupuestos/{budget_request.id}",
        entity_type="BudgetOffer",
        entity_id=offer.id,
        prioridad=PRIORIDAD_ACCION_REQUERIDA,
        requiere_accion=True,
    )


def notify_budget_cancelled(budget_request):
    registrar_evento(
        user_id=budget_request.cliente_id,
        actor_user_id=budget_request.cliente_id,
        tipo=TIPO_PRESUPUESTO_CANCELADO,
        categoria=CATEGORIA_PRESUPUESTOS,
        titulo="Cancelaste una solicitud de presupuesto",
        mensaje=f"{budget_request.titulo} ya no recibira nuevas ofertas.",
        url_destino="/presupuestos/mis-solicitudes?estado=canceladas",
        entity_type="BudgetRequest",
        entity_id=budget_request.id,
    )

    notified_professionals = {
        offer.professional_user_id
        for offer in budget_request.offers
        if offer.professional_user_id
    }
    for professional_user_id in notified_professionals:
        registrar_evento(
            user_id=professional_user_id,
            actor_user_id=budget_request.cliente_id,
            tipo=TIPO_PRESUPUESTO_CANCELADO,
            categoria=CATEGORIA_PRESUPUESTOS,
            titulo="Una solicitud fue cancelada",
            mensaje=f"La solicitud {budget_request.titulo} fue cancelada por el cliente.",
            url_destino=f"/presupuestos/{budget_request.id}",
            entity_type="BudgetRequest",
            entity_id=budget_request.id,
        )


def notify_emergency_created(emergency_request):
    registrar_evento(
        user_id=emergency_request.cliente_id,
        actor_user_id=emergency_request.cliente_id,
        tipo=TIPO_EMERGENCIA_PUBLICADA,
        categoria=CATEGORIA_EMERGENCIAS,
        titulo="Publicaste una emergencia",
        mensaje=f"Tu emergencia de {emergency_request.categoria} en {emergency_request.zona} quedo registrada.",
        url_destino="/emergencias/directorio",
        entity_type="EmergencyRequest",
        entity_id=emergency_request.id,
        prioridad=PRIORIDAD_ACCION_REQUERIDA,
        requiere_accion=True,
    )


def notify_proposal_created(proposal):
    registrar_evento(
        user_id=proposal.owner_user_id or proposal.cliente_id,
        actor_user_id=proposal.owner_user_id or proposal.cliente_id,
        tipo=TIPO_PROPUESTA_PUBLICADA,
        categoria=CATEGORIA_PROPUESTAS,
        titulo="Publicaste una propuesta",
        mensaje=f"{proposal.titulo} ya puede recibir postulaciones.",
        url_destino=f"/propuestas/{proposal.id}",
        entity_type="ProposalRequest",
        entity_id=proposal.id,
    )


def notify_proposal_application_created(application):
    proposal = application.proposal
    owner_id = proposal.owner_user_id or proposal.cliente_id
    professional_name = user_display_name(application.professional_user_id, "Un profesional")

    registrar_evento(
        user_id=application.professional_user_id,
        actor_user_id=application.professional_user_id,
        tipo=TIPO_PROPUESTA_POSTULACION_ENVIADA,
        categoria=CATEGORIA_PROPUESTAS,
        titulo="Te postulaste a una propuesta",
        mensaje=f"Tu postulacion para {proposal.titulo} quedo registrada.",
        url_destino=f"/propuestas/{proposal.id}",
        entity_type="ProposalApplication",
        entity_id=application.id,
    )
    registrar_evento(
        user_id=owner_id,
        actor_user_id=application.professional_user_id,
        tipo=TIPO_PROPUESTA_POSTULACION_RECIBIDA,
        categoria=CATEGORIA_PROPUESTAS,
        titulo="Recibiste una postulacion",
        mensaje=f"{professional_name} se postulo a {proposal.titulo}.",
        url_destino=f"/propuestas/{proposal.id}",
        entity_type="ProposalApplication",
        entity_id=application.id,
        prioridad=PRIORIDAD_ACCION_REQUERIDA,
        requiere_accion=True,
    )


def notify_proposal_application_status(application, tipo, title, message):
    proposal = application.proposal
    owner_id = proposal.owner_user_id or proposal.cliente_id

    registrar_evento(
        user_id=owner_id,
        actor_user_id=owner_id,
        tipo=tipo,
        categoria=CATEGORIA_PROPUESTAS,
        titulo=title,
        mensaje=message,
        url_destino=f"/propuestas/{proposal.id}",
        entity_type="ProposalApplication",
        entity_id=application.id,
    )
    registrar_evento(
        user_id=application.professional_user_id,
        actor_user_id=owner_id,
        tipo=tipo,
        categoria=CATEGORIA_PROPUESTAS,
        titulo=title,
        mensaje=message,
        url_destino=f"/propuestas/{proposal.id}",
        entity_type="ProposalApplication",
        entity_id=application.id,
        prioridad=PRIORIDAD_INFO,
    )


def notify_proposal_accepted(application):
    notify_proposal_application_status(
        application,
        TIPO_PROPUESTA_POSTULACION_ACEPTADA,
        "Postulacion aceptada",
        f"La postulacion para {application.proposal.titulo} fue aceptada.",
    )


def notify_proposal_discarded(application):
    notify_proposal_application_status(
        application,
        TIPO_PROPUESTA_POSTULACION_DESCARTADA,
        "Postulacion descartada",
        f"La postulacion para {application.proposal.titulo} fue descartada.",
    )


def notify_proposal_cancelled(proposal):
    owner_id = proposal.owner_user_id or proposal.cliente_id
    registrar_evento(
        user_id=owner_id,
        actor_user_id=owner_id,
        tipo=TIPO_PROPUESTA_CANCELADA,
        categoria=CATEGORIA_PROPUESTAS,
        titulo="Cancelaste una propuesta",
        mensaje=f"{proposal.titulo} ya no recibira postulaciones.",
        url_destino=f"/propuestas/{proposal.id}",
        entity_type="ProposalRequest",
        entity_id=proposal.id,
    )

    notified_professionals = {
        application.professional_user_id
        for application in proposal.applications
        if application.professional_user_id
    }
    for professional_user_id in notified_professionals:
        registrar_evento(
            user_id=professional_user_id,
            actor_user_id=owner_id,
            tipo=TIPO_PROPUESTA_CANCELADA,
            categoria=CATEGORIA_PROPUESTAS,
            titulo="Una propuesta fue cancelada",
            mensaje=f"La propuesta {proposal.titulo} fue cancelada por el publicador.",
            url_destino=f"/propuestas/{proposal.id}",
            entity_type="ProposalRequest",
            entity_id=proposal.id,
        )
