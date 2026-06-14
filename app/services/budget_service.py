from datetime import datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import IntegrityError

from app import db
from app.models.budget_offer import BudgetOffer
from app.models.budget_request import BudgetRequest
from app.models.professional import Professional
from app.services.subscription_service import has_pro_access


MAX_OFFERS_PER_REQUEST = 6
WORK_MONTHLY_OFFER_LIMIT = 9


def create_budget_request(
    cliente_id,
    categoria,
    titulo,
    descripcion,
    zona,
    fecha_estimada=None,
    urgencia="NORMAL",
):
    budget_request = BudgetRequest(
        cliente_id=cliente_id,
        categoria=categoria,
        titulo=titulo,
        descripcion=descripcion,
        zona=zona,
        fecha_estimada=fecha_estimada,
        urgencia=urgencia,
    )

    db.session.add(budget_request)
    db.session.commit()

    return budget_request


def get_budget_request_by_id(budget_request_id):
    return db.session.get(BudgetRequest, budget_request_id)


def get_open_budget_requests(categoria=None, zona=None):
    query = BudgetRequest.query.filter(
        BudgetRequest.estado.in_(("ABIERTO", "COTIZANDO")),
    )

    if categoria:
        query = query.filter(BudgetRequest.categoria.ilike(f"%{categoria}%"))
    if zona:
        query = query.filter(BudgetRequest.zona.ilike(f"%{zona}%"))

    return query.order_by(BudgetRequest.fecha_creacion.desc()).all()


def get_budget_offers(budget_request_id):
    return (
        BudgetOffer.query
        .filter_by(budget_request_id=budget_request_id)
        .order_by(BudgetOffer.monto.asc(), BudgetOffer.fecha_creacion.asc())
        .all()
    )


def get_professional_monthly_offer_count(professional_user_id, now=None):
    now = now or datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)

    return (
        BudgetOffer.query
        .filter(
            BudgetOffer.professional_user_id == professional_user_id,
            BudgetOffer.fecha_creacion >= month_start,
            BudgetOffer.fecha_creacion < next_month,
        )
        .count()
    )


def get_offer_allowance(professional_user_id):
    if has_pro_access(professional_user_id):
        return {
            "is_pro": True,
            "used": get_professional_monthly_offer_count(professional_user_id),
            "limit": None,
            "remaining": None,
        }

    used = get_professional_monthly_offer_count(professional_user_id)
    return {
        "is_pro": False,
        "used": used,
        "limit": WORK_MONTHLY_OFFER_LIMIT,
        "remaining": max(WORK_MONTHLY_OFFER_LIMIT - used, 0),
    }


def create_budget_offer(
    budget_request_id,
    professional_user_id,
    monto,
    mensaje,
    plazo_estimado,
    condiciones=None,
):
    professional = Professional.query.filter_by(user_id=professional_user_id).first()
    if professional is None or not professional.perfil_completo:
        raise ValueError("Necesitas completar tu perfil profesional para ofertar")

    try:
        amount = Decimal(str(monto))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("El monto ingresado no es valido") from None

    if amount <= 0:
        raise ValueError("El monto debe ser mayor que cero")

    budget_request = (
        BudgetRequest.query
        .filter_by(id=budget_request_id)
        .with_for_update()
        .first()
    )
    if budget_request is None:
        raise ValueError("Solicitud de presupuesto no encontrada")
    if budget_request.cliente_id == professional_user_id:
        raise ValueError("No podes presupuestar tu propia solicitud")
    if budget_request.estado not in ("ABIERTO", "COTIZANDO"):
        raise ValueError("Esta solicitud ya no recibe presupuestos")

    existing_offer = BudgetOffer.query.filter_by(
        budget_request_id=budget_request.id,
        professional_id=professional.id,
    ).first()
    if existing_offer is not None:
        raise ValueError("Ya enviaste un presupuesto para esta solicitud")

    if BudgetOffer.query.filter_by(budget_request_id=budget_request.id).count() >= MAX_OFFERS_PER_REQUEST:
        raise ValueError("La solicitud ya alcanzo el maximo de 6 presupuestos")

    allowance = get_offer_allowance(professional_user_id)
    if not allowance["is_pro"] and allowance["remaining"] <= 0:
        raise ValueError(
            "Alcanzaste el limite WORK de 9 presupuestos mensuales. "
            "Podes pasar a PRO para enviar presupuestos sin limite."
        )

    offer = BudgetOffer(
        budget_request_id=budget_request.id,
        professional_id=professional.id,
        professional_user_id=professional_user_id,
        monto=amount,
        mensaje=mensaje,
        plazo_estimado=plazo_estimado,
        condiciones=condiciones,
    )
    budget_request.estado = "COTIZANDO"
    db.session.add(offer)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("Ya enviaste un presupuesto para esta solicitud") from None

    return offer


def award_budget_offer(budget_request_id, offer_id, cliente_id):
    budget_request = (
        BudgetRequest.query
        .filter_by(id=budget_request_id)
        .with_for_update()
        .first()
    )
    if budget_request is None:
        raise ValueError("Solicitud de presupuesto no encontrada")
    if budget_request.cliente_id != cliente_id:
        raise PermissionError("Solo el cliente dueño puede adjudicar esta solicitud")
    if budget_request.estado == "ADJUDICADA":
        raise ValueError("Esta solicitud ya fue adjudicada")
    if budget_request.estado == "CERRADO":
        raise ValueError("Esta solicitud esta cerrada")

    offer = BudgetOffer.query.filter_by(
        id=offer_id,
        budget_request_id=budget_request.id,
    ).first()
    if offer is None:
        raise ValueError("El presupuesto seleccionado no pertenece a esta solicitud")

    offer.estado = "ADJUDICADO"
    budget_request.estado = "ADJUDICADA"
    db.session.commit()

    return offer


def get_client_budget_requests(cliente_id):
    return (
        BudgetRequest.query
        .filter_by(cliente_id=cliente_id)
        .order_by(BudgetRequest.fecha_creacion.desc())
        .all()
    )


def update_budget_status(budget_request_id, estado):
    if estado not in BudgetRequest.ESTADOS:
        raise ValueError("Estado de presupuesto invalido")

    budget_request = BudgetRequest.query.get(budget_request_id)

    if budget_request is None:
        return None

    budget_request.estado = estado
    db.session.commit()

    return budget_request
