from flask import Blueprint, Response, current_app, redirect, render_template, session, url_for

from app import db

from app.services.mercadopago_order_creation_adapter import MercadoPagoOrderConfigurationError
from app.services.payment_order_application_service import PaymentOrderExpiredError
from app.services.payment_order_delivery_service import PaymentOrderUnavailableError
from app.services.psp_payment_order_contract import (
    PaymentOrderCreationUncertainError, PaymentOrderIdempotencyConflictError,
)
from app.utils.decorators import login_required, role_required


payment_order_delivery = Blueprint("payment_order_delivery", __name__)


def _service():
    if current_app.config.get("CHECKOUT_PRO_DELIVERY_ENABLED") is not True:
        raise PaymentOrderUnavailableError
    service = current_app.extensions.get("payment_order_delivery_service")
    if service is None:
        raise PaymentOrderUnavailableError
    return service


def _execute(operation):
    # Public responses contain only classifications, never exception arguments.
    failure = None
    try:
        return operation()
    except PermissionError:
        failure = ("Acceso no autorizado", 403)
    except (PaymentOrderIdempotencyConflictError, PaymentOrderCreationUncertainError):
        failure = ("La orden está bloqueada y requiere revisión", 409)
    except PaymentOrderExpiredError:
        failure = ("La orden no está vigente", 410)
    except (PaymentOrderUnavailableError, MercadoPagoOrderConfigurationError):
        failure = ("Checkout no disponible", 503)
    except ValueError:
        failure = ("Solicitud inválida", 400)
    except Exception:
        failure = ("Error interno", 500)
    message, status = failure
    return render_template("payment_order_checkout.html", checkout=None, error_message=message), status


@payment_order_delivery.route("/contratacion/<int:id>/orden-de-cobro", methods=["POST"])
@login_required
@role_required("PROFESIONAL")
def create_order(id):
    def operation():
        # Session decorators queried through the request-scoped ORM session.
        # Release it before 4B commits its claim and performs the external call.
        db.session.remove()
        _service().create_order(actor_user_id=session["user_id"], contract_request_id=id)
        return redirect(url_for("payment_order_delivery.checkout", id=id), code=303)
    return _execute(operation)


@payment_order_delivery.route("/contratacion/<int:id>/orden-de-cobro", methods=["GET"])
@login_required
@role_required("PROFESIONAL")
def checkout(id):
    def operation():
        service = _service()
        result = service.get_checkout(actor_user_id=session["user_id"], contract_request_id=id)
        page = render_template("payment_order_checkout.html", checkout=result, contract_id=id)
        service.ensure_unexpired(result)
        return page
    return _execute(operation)


@payment_order_delivery.route("/contratacion/<int:id>/orden-de-cobro/qr.png", methods=["GET"])
@login_required
@role_required("PROFESIONAL")
def qr_png(id):
    def operation():
        image = _service().get_qr_png(actor_user_id=session["user_id"], contract_request_id=id)
        return Response(image, mimetype="image/png")
    return _execute(operation)
