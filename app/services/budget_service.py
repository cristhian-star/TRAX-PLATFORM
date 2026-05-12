from app import db
from app.models.budget_request import BudgetRequest


def create_budget_request(cliente_id, categoria, descripcion, zona):
    budget_request = BudgetRequest(
        cliente_id=cliente_id,
        categoria=categoria,
        descripcion=descripcion,
        zona=zona
    )

    db.session.add(budget_request)
    db.session.commit()

    return budget_request


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
