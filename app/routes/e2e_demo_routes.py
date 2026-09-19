"""Visible QA walkthrough; blueprint is absent outside the disposable demo."""
from datetime import datetime, timezone

from flask import Blueprint, abort, current_app, redirect, render_template, session, url_for, Response

from app import db
from app.models.contract_request import ContractRequest
from app.models.payment_order import PaymentOrder
from app.models.user import User
from app.services.simulated_mercadopago_demo import (
    DEMO_CONTRACT_KEY, DEMO_ORIGIN, DEMO_POLICY, DEMO_COMMISSION,
    delivery, enabled, progress, simulate_payment, apply_effect,
)
from app.utils.decorators import login_required


e2e_demo = Blueprint("e2e_demo", __name__, url_prefix="/dev/e2e")


@e2e_demo.before_request
def _guard():
    if not enabled(current_app.config):
        abort(404)


def _contract():
    contract = ContractRequest.query.filter_by(descripcion=DEMO_CONTRACT_KEY).one_or_none()
    if contract is None:
        abort(404)
    if session.get("user_id") not in (contract.cliente_id, contract.professional_user_id):
        abort(403)
    actor = db.session.get(User, session["user_id"])
    if actor is None or actor.estado != "ACTIVO":
        abort(403)
    expected_role = "CLIENTE" if actor.id == contract.cliente_id else "PROFESIONAL"
    if actor.rol != expected_role:
        abort(403)
    return contract


@e2e_demo.get("/")
@login_required
def dashboard():
    contract = _contract()
    state = progress(contract.id)
    page = render_template(
        "e2e_demo.html", contract=contract, state=state,
        is_client=session["user_id"] == contract.cliente_id,
        policy=DEMO_POLICY, commission=DEMO_COMMISSION,
    )
    response = Response(page)
    response.headers["Cache-Control"] = "no-store, private"
    return response


@e2e_demo.post("/order")
@login_required
def create_order():
    contract = _contract()
    if session["user_id"] != contract.professional_user_id or contract.estado != "CONFIRMADA":
        abort(403)
    db.session.remove()
    try:
        delivery().create_order(actor_user_id=session["user_id"], contract_request_id=contract.id)
    except Exception:
        abort(409)
    return redirect(url_for("e2e_demo.order"), code=303)


@e2e_demo.get("/order")
@login_required
def order():
    contract = _contract()
    if session["user_id"] != contract.professional_user_id:
        abort(403)
    db.session.remove()
    try:
        checkout = delivery().get_checkout(actor_user_id=session["user_id"], contract_request_id=contract.id)
    except Exception:
        abort(410)
    response = Response(render_template("e2e_demo_checkout.html", checkout=checkout, contract=contract))
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@e2e_demo.get("/order/qr.png")
@login_required
def qr():
    contract = _contract()
    if session["user_id"] != contract.professional_user_id:
        abort(403)
    db.session.remove()
    try:
        image = delivery().get_qr_png(actor_user_id=session["user_id"], contract_request_id=contract.id)
    except Exception:
        abort(410)
    response = Response(image, mimetype="image/png")
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@e2e_demo.get("/checkout/<external_id>")
@login_required
def local_checkout(external_id):
    contract = _contract()
    if session["user_id"] != contract.cliente_id:
        abort(403)
    if not external_id.startswith("sim-"):
        abort(404)
    order = PaymentOrder.query.filter_by(external_order_id=external_id, live_mode=False).one_or_none()
    if order is None or order.provider != "mercadopago" or order.checkout_url != f"{DEMO_ORIGIN}/dev/e2e/checkout/{external_id}":
        abort(404)
    if order.obligation.contract_request_id != contract.id:
        abort(403)
    if order.status != "ACTIVE" or order.expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        abort(410)
    response = Response(render_template("e2e_demo_payment.html", contract=contract, order=order))
    response.headers["Cache-Control"] = "no-store, private"
    return response


@e2e_demo.post("/checkout/<external_id>/approve")
@login_required
def approve(external_id):
    local_checkout(external_id)
    contract = _contract()
    db.session.remove()
    try:
        simulate_payment(contract.id)
    except Exception:
        abort(409)
    return redirect(url_for("e2e_demo.dashboard"), code=303)


@e2e_demo.post("/apply")
@login_required
def apply():
    contract = _contract()
    if session["user_id"] != contract.professional_user_id:
        abort(403)
    db.session.remove()
    try:
        apply_effect(contract.id)
    except Exception:
        abort(409)
    return redirect(url_for("e2e_demo.dashboard"), code=303)
