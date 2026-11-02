"""Owned, read-only aggregates. Rolling UTC instants, not calendar-day cohorts."""
from datetime import datetime, timedelta, timezone
from flask import abort, current_app
from sqlalchemy import func, case
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models.professional import Professional
from app.models.budget_offer import BudgetOffer
from app.models.proposal_application import ProposalApplication
from app.models.contract_request import ContractRequest
from app.services.professional_workspace_service import owned_contracts

TABS = (("resumen", "Resumen"), ("perfil", "Perfil y alcance"),
        ("actividad", "Actividad comercial"), ("demanda", "Demanda y precios"))


def statistics_context(user_id, args, now=None):
    tab, period = args.get("tab", "resumen"), args.get("periodo", "30")
    if (len(args.getlist("tab")) > 1 or len(args.getlist("periodo")) > 1
            or tab not in dict(TABS) or period not in ("7", "30", "90")):
        abort(400)
    # UTC storage is naive in the existing models. Rolling durations are invariant
    # under Buenos Aires timezone conversion; no local calendar-day boundaries.
    end = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(tzinfo=None)
    start = end - timedelta(days=int(period))
    context = dict(tab=tab, tabs=TABS, period=int(period), statistics_error=False,
                   groups=[], metrics=[], evolution=[], start=start, end=end)
    if tab in ("perfil", "demanda"):
        return context
    try:
        specifications = (
            (BudgetOffer, BudgetOffer.fecha_creacion, "Presupuestos enviados"),
            (ProposalApplication, ProposalApplication.created_at, "Postulaciones enviadas"),
        )
        for model, date, label in specifications:
            rows = dict(db.session.query(model.estado, func.count(model.id)).join(
                Professional, model.professional_id == Professional.id).filter(
                model.professional_user_id == user_id, Professional.user_id == user_id,
                date >= start, date < end).group_by(model.estado).all())
            context["groups"].append(dict(label=label, rows=[(state, rows.get(state, 0)) for state in model.ESTADOS]))
            context["metrics"].append(dict(label=label, value=sum(rows.values())))
        contracts = owned_contracts(user_id)
        rows = dict(contracts.with_entities(ContractRequest.estado, func.count(ContractRequest.id)).filter(
            ContractRequest.fecha_creacion >= start, ContractRequest.fecha_creacion < end
        ).group_by(ContractRequest.estado).all())
        context["groups"].append(dict(label="Solicitudes de contratación recibidas", rows=[
            (state, rows.get(state, 0)) for state in ContractRequest.ESTADOS]))
        context["metrics"].append(dict(label="Solicitudes de contratación recibidas", value=sum(rows.values())))
        buckets = [(offset, min(offset + 7, int(period))) for offset in range(0, int(period), 7)]
        columns = [func.sum(case((
            (ContractRequest.fecha_creacion >= end - timedelta(days=older)) &
            (ContractRequest.fecha_creacion < end - timedelta(days=newer)), 1), else_=0))
            for newer, older in buckets]
        counts = contracts.with_entities(*columns).filter(
            ContractRequest.fecha_creacion >= start, ContractRequest.fecha_creacion < end).one()
        context["evolution"] = [dict(newer=newer, older=older, count=int(count or 0))
                                for (newer, older), count in reversed(list(zip(buckets, counts)))]
        confirmed = contracts.filter(ContractRequest.estado == "CONFIRMADA",
            ContractRequest.confirmed_at >= start, ContractRequest.confirmed_at < end).count()
        context["metrics"].append(dict(label="Finalización confirmada por el cliente", value=confirmed))
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Professional statistics read failed")
        context.update(statistics_error=True, groups=[], metrics=[], evolution=[])
    return context
