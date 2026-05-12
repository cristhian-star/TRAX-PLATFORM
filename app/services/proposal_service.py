from app import db
from app.models.proposal_request import ProposalRequest


OPEN_STATUSES = (
    "ABIERTA",
    "RECIBIENDO_PROPUESTAS",
)


def create_proposal_request(
    cliente_id,
    categoria,
    descripcion,
    presupuesto_estimado=None,
    fecha_limite=None
):
    proposal_request = ProposalRequest(
        cliente_id=cliente_id,
        categoria=categoria,
        descripcion=descripcion,
        presupuesto_estimado=presupuesto_estimado,
        fecha_limite=fecha_limite
    )

    db.session.add(proposal_request)
    db.session.commit()

    return proposal_request


def get_open_proposals():
    return (
        ProposalRequest.query
        .filter(ProposalRequest.estado.in_(OPEN_STATUSES))
        .order_by(ProposalRequest.id.desc())
        .all()
    )


def close_proposal(proposal_request_id):
    proposal_request = ProposalRequest.query.get(proposal_request_id)

    if proposal_request is None:
        return None

    proposal_request.estado = "CERRADA"
    db.session.commit()

    return proposal_request
