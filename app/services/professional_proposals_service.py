"""Professional presentation over the canonical proposal domain; reads only."""
from flask import abort, request, session, url_for
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app import db
from app.models.user import User
from app.models.proposal_request import ProposalRequest
from app.models.proposal_application import ProposalApplication
from app.models.contract_request import ContractRequest
from app.services.proposal_portal_service import build_proposal_portal
from app.services.professional_workspace_service import build_workspace, owned_contracts
from app.services.user_service import is_user_active


VIEWS = ("disponibles", "postulaciones", "publicaciones")


def proposal_navigation():
    user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    private = is_user_active(user) and user.rol == "PROFESIONAL"
    view = request.values.get("vista", "disponibles")
    if view not in VIEWS:
        view = "disponibles"
    return dict(proposal_workspace=private, proposal_view=view,
                proposal_back=url_for("main.profesional_marketplace", vista=view) if private
                else url_for("operations.marketplace_propuestas"),
                workspace=build_workspace(user.id) if private else None)


def build_professional_proposals(args, user_id):
    view = args.get("vista", "disponibles")
    if len(args.getlist("vista")) > 1 or view not in VIEWS:
        abort(400)
    if view == "disponibles":
        result = build_proposal_portal(args, user_id, "main.profesional_marketplace")
        result.update(view=view, rows=[])
        return result

    raw = args.get("page", "1")
    if len(args.getlist("page")) > 1 or not raw.isascii() or not raw.isdecimal() or len(raw) > 4 or not 1 <= int(raw) <= 1000:
        abort(400)
    page, size = int(raw), 12
    if view == "postulaciones":
        query = ProposalApplication.query.options(joinedload(ProposalApplication.proposal)).filter_by(
            professional_user_id=user_id).order_by(ProposalApplication.created_at.desc(), ProposalApplication.id.desc())
    else:
        query = ProposalRequest.query.filter(func.coalesce(ProposalRequest.owner_user_id, ProposalRequest.cliente_id) == user_id).order_by(
            ProposalRequest.created_at.desc(), ProposalRequest.id.desc())
    total = query.count()
    records = query.offset((page - 1) * size).limit(size).all()
    ids = [row.id for row in records]
    contracts = {}
    counts = {}
    if view == "postulaciones" and ids:
        contracts = {c.proposal_application_id: c.id for c in owned_contracts(user_id).filter(
            ContractRequest.source_type == "PROPOSAL", ContractRequest.proposal_application_id.in_(ids)).all()}
    elif ids:
        counts = dict(db.session.query(ProposalApplication.proposal_id, func.count(ProposalApplication.id)).filter(
            ProposalApplication.proposal_id.in_(ids)).group_by(ProposalApplication.proposal_id).all())
    rows = [dict(proposal=r.proposal if view == "postulaciones" else r,
                 state=r.estado, date=r.created_at, count=counts.get(r.id, 0),
                 contract_id=contracts.get(r.id)) for r in records]
    pages = (total + size - 1) // size
    def link(number):
        return url_for("main.profesional_marketplace", vista=view, page=number)
    return dict(view=view, cards=[], rows=rows, total=total, page=page, pages=pages,
                previous_url=link(page-1) if 1 < page <= pages else None,
                next_url=link(page+1) if page < pages else None, first_url=link(1))
