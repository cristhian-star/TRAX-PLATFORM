"""Read-only presentation for the explicitly composed, isolated collection preview."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from flask import current_app, abort
from itsdangerous import URLSafeTimedSerializer, BadSignature
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models.contract_request import ContractRequest
from app.models.professional import Professional
from app.models.user import User
from app.models.payment_order import PaymentOrder
from app.models.payment_obligation import PaymentObligation
from app.models.payment_order_reservation import PaymentOrderReservation
from app.services.actor_policy_service import require_active_actor


def simulation_available():
    runtime = current_app.extensions.get("isolated_collection_runtime")
    if runtime is None:
        return False
    return (current_app.config.get("TESTING") is True
            and current_app.config.get("ENV_NAME") == "testing"
            and current_app.config.get("CHECKOUT_PRO_DELIVERY_ENABLED") is True
            and runtime.valid(db.engine)
            and current_app.extensions.get("payment_order_delivery_service") is runtime.delivery)


def _owned(user_id):
    require_active_actor(user_id, ("PROFESIONAL",), session=db.session)
    return ContractRequest.query.join(Professional, ContractRequest.professional_id == Professional.id).filter(
        ContractRequest.professional_user_id == user_id, Professional.user_id == user_id)


def _amount(contract):
    try:
        amount = Decimal(str(contract.precio_acordado))
        with localcontext() as context:
            context.prec = 70
            if not amount.is_finite() or not 0 < amount < Decimal("1e62") or amount != amount.quantize(Decimal(".01")):
                return None
        return format(amount, ".2f")
    except (InvalidOperation, ValueError):
        return None


def _card(contract):
    return {"id": contract.id, "service": contract.servicio, "amount": _amount(contract),
            "customer": "Cliente #" + str(contract.cliente_id), "version": contract.version}


def _page(args):
    values = args.getlist("page")
    if len(values) > 1 or (values and (not values[0].isascii() or not values[0].isdigit() or len(values[0]) > 6)):
        abort(400)
    page = int(values[0]) if values else 1
    if page < 1 or page > 10000:
        abort(400)
    return page


def selector(user_id, args):
    page = _page(args)
    try:
        records = _owned(user_id).filter(ContractRequest.estado == "CONFIRMADA",
            ContractRequest.precio_acordado > 0).order_by(ContractRequest.id.desc()).offset((page-1)*20).limit(21).all()
        rows = [_card(c) for c in records[:20] if _amount(c) is not None]
        return {"rows": rows, "page": page, "more": len(records)>20, "error": False}
    except SQLAlchemyError:
        current_app.logger.exception("Collection selector failed")
        return {"rows": [], "page": page, "more": False, "error": True}


def review(user_id, contract_id):
    contract = _owned(user_id).filter(ContractRequest.id == contract_id,
                                     ContractRequest.estado == "CONFIRMADA").one_or_none()
    if contract is None or _amount(contract) is None:
        abort(403)
    card = _card(contract)
    reservation = db.session.query(PaymentOrderReservation).join(PaymentObligation).filter(
        PaymentObligation.contract_request_id == contract.id).one_or_none()
    card["blocked"] = bool(reservation and reservation.status in ("CALL_IN_PROGRESS", "UNCERTAIN"))
    return card


def _signer():
    return URLSafeTimedSerializer(current_app.secret_key, salt="collection-review-v1")


def review_token(user_id, card):
    return _signer().dumps([user_id, card["id"], card["amount"], card["version"]])


def check_review(user_id, contract_id, token):
    try:
        expected = _signer().loads(token or "", max_age=1800)
    except BadSignature:
        abort(409, description="Revisá nuevamente el trabajo antes de generar la orden simulada.")
    card = review(user_id, contract_id)
    if expected != [user_id, card["id"], card["amount"], card["version"]]:
        abort(409, description="El trabajo cambió. Revisá nuevamente el importe antes de continuar.")
    return card


def history(user_id, args):
    page = _page(args)
    try:
        require_active_actor(user_id, ("PROFESIONAL",), session=db.session)
        records = db.session.query(PaymentOrder, ContractRequest.id).join(
            PaymentObligation, PaymentOrder.obligation_id == PaymentObligation.id).join(
            ContractRequest, PaymentObligation.contract_request_id == ContractRequest.id).join(
            Professional, ContractRequest.professional_id == Professional.id).filter(
            Professional.user_id == user_id, ContractRequest.professional_user_id == user_id,
            PaymentOrder.professional_id == Professional.id).order_by(
            PaymentOrder.created_at.desc(), PaymentOrder.id.desc()).offset((page-1)*20).limit(21).all()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        rows = [{"id": order.id, "contract_id": cid, "amount": format(order.amount, ".2f"),
                 "status": order.status, "expired": order.expires_at <= now,
                 "created": order.created_at, "expires": order.expires_at} for order,cid in records[:20]]
        blocked = db.session.query(PaymentOrderReservation, ContractRequest.id).join(
            PaymentObligation, PaymentOrderReservation.obligation_id == PaymentObligation.id).join(
            ContractRequest, PaymentObligation.contract_request_id == ContractRequest.id).join(
            Professional, ContractRequest.professional_id == Professional.id).filter(
            Professional.user_id == user_id, ContractRequest.professional_user_id == user_id,
            PaymentOrderReservation.professional_id == Professional.id,
            PaymentOrderReservation.actor_user_id == user_id,
            PaymentOrderReservation.status.in_(("CALL_IN_PROGRESS", "UNCERTAIN"))).order_by(
            PaymentOrderReservation.id.desc()).limit(20).all()
        return {"rows": rows, "blocked": [{"contract_id": cid, "status": r.status} for r,cid in blocked],
                "page": page, "more": len(records)>20, "error": False}
    except SQLAlchemyError:
        current_app.logger.exception("Collection history failed")
        return {"rows": [], "page": page, "more": False, "error": True}
