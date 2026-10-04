"""Read-only public portal; no new domain rules or private owner fields."""
from flask import abort, url_for
from sqlalchemy import func
from app import db
from app.models.proposal_request import ProposalRequest
from app.models.proposal_application import ProposalApplication
from app.models.user import User
from app.services.proposal_service import open_proposals_query
from app.services.proposal_eligibility_service import proposal_application_eligibility
from app.services.user_service import is_user_active


def build_proposal_portal(args, user_id):
    names = ("industria", "categoria", "rubro", "ubicacion")
    filters = {}
    for name in (*names, "page", "per_page"):
        if len(args.getlist(name)) > 1:
            abort(400)
        value = args.get(name, "").strip()
        if len(value) > 120:
            abort(400)
        if name in names:
            filters[name] = value

    def positive(name, default, maximum):
        value = args.get(name, str(default))
        if not value.isascii() or not value.isdecimal() or len(value) > 6:
            abort(400)
        result = int(value)
        if not 1 <= result <= maximum:
            abort(400)
        return result

    page = positive("page", 1, 1000)
    per_page = positive("per_page", 12, 50)
    query = open_proposals_query(**filters)
    total = query.order_by(None).count()
    proposals = query.offset((page - 1) * per_page).limit(per_page).all()
    ids = [p.id for p in proposals]
    counts = dict(db.session.query(ProposalApplication.proposal_id, func.count(ProposalApplication.id))
                  .filter(ProposalApplication.proposal_id.in_(ids))
                  .group_by(ProposalApplication.proposal_id).all()) if ids else {}
    eligibility = proposal_application_eligibility(user_id)
    applied = {row[0] for row in db.session.query(ProposalApplication.proposal_id).filter(
        ProposalApplication.proposal_id.in_(ids),
        ProposalApplication.professional_user_id == user_id).all()} if user_id and ids else set()
    cards = []
    for p in proposals:
        cards.append(dict(id=p.id, title=p.titulo or p.categoria,
                          description=((p.descripcion or "")[:237] + "…") if len(p.descripcion or "") > 240 else (p.descripcion or ""),
                          category=p.categoria, trade=p.rubro, specialty=p.especialidad,
                          location=p.ubicacion, published=p.created_at,
                          budget=p.presupuesto_estimado, applications=counts.get(p.id, 0),
                          can_apply=eligibility.eligible and (p.owner_user_id or p.cliente_id) != user_id and p.id not in applied,
                          applied=p.id in applied))
    # Options come from actual published records, not a parallel taxonomy catalog.
    options = {}
    for name in ("industria", "categoria"):
        column = getattr(ProposalRequest, name)
        options[name] = [row[0] for row in db.session.query(column).filter(
            ProposalRequest.estado == "PUBLICADA", column.isnot(None), column != "")
            .distinct().order_by(column).all()]
        if filters[name] and filters[name] not in options[name]:
            options[name].append(filters[name])
    pages = (total + per_page - 1) // per_page
    def page_url(number):
        return url_for("operations.marketplace_propuestas", **{k:v for k,v in filters.items() if v}, page=number, per_page=per_page)
    labels = {"industria": "Industria", "categoria": "Categoría", "rubro": "Rubro", "ubicacion": "Ubicación"}
    active_filters = [dict(name=name, label=labels[name], value=value,
                          remove_url=url_for("operations.marketplace_propuestas",
                              **{k: v for k, v in filters.items() if v and k != name},
                              per_page=per_page))
                      for name, value in filters.items() if value]
    user = db.session.get(User, user_id) if user_id else None
    return dict(active_filters=active_filters, cards=cards, filters=filters, options=options, total=total,
                page=page, pages=pages, per_page=per_page,
                previous_url=page_url(page-1) if 1 < page <= pages else None,
                next_url=page_url(page+1) if page < pages else None,
                first_url=page_url(1), eligibility=eligibility,
                can_create=is_user_active(user), has_filters=any(filters.values()))
