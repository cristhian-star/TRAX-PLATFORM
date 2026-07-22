from app.services.budget_service import get_budget_request_by_id
from app.services.proposal_service import get_proposal_by_id


def get_budget_request_or_error(budget_request_id):
    budget_request = get_budget_request_by_id(budget_request_id)
    if budget_request is None:
        raise LookupError("Solicitud de presupuesto no encontrada")

    return budget_request


def require_budget_owner(budget_request, user_id):
    if budget_request.cliente_id != user_id:
        raise PermissionError("Solo el cliente dueno puede operar esta solicitud")


def get_proposal_or_error(proposal_id):
    proposal = get_proposal_by_id(proposal_id)
    if proposal is None:
        raise LookupError("Propuesta no encontrada")

    return proposal


def proposal_owner_id(proposal):
    return proposal.owner_user_id or proposal.cliente_id


def require_proposal_owner(proposal, user_id):
    if proposal_owner_id(proposal) != user_id:
        raise PermissionError("Solo el publicador puede operar esta propuesta")
